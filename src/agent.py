"""
src/agent.py
FIN-SIGHT – Main research orchestrator.
Coordinates all modules: mode classification, clarification, Gemini API call,
contradiction detection, confidence scoring, scenario generation, cost tracking,
and structured output formatting.
"""

from __future__ import annotations
import os
import re
import time
import warnings
from typing import Any

warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", message=".*google.generativeai.*")

from groq import Groq
import google.generativeai as genai

from src.config import (
    GROQ_API_KEY, GROQ_MODEL_NAME,
    GEMINI_API_KEY, MODEL_NAME,
    ACTIVE_BACKEND, GENERATION_CONFIG,
)
from src.memory import load_memory, update_preference, memory_summary
from src.mode_classifier import classify_mode, explain_classification
from src.clarification import (
    needs_clarification,
    get_clarification_questions,
    format_clarification_prompt,
    extract_preferences_from_input,
)
from src.confidence_engine import calculate_confidence, ConfidenceResult
from src.contradiction_detector import detect_contradictions
from src.scenario_engine import run_base_downside_stress, run_scenarios, ScenarioRow
from src.cost_tracker import Timer, estimate_cost, UsageSummary
from src.output_formatter import (
    format_quick_mode,
    format_deep_mode,
    format_scenario_only,
)
from prompts.system_prompt import SYSTEM_PROMPT
from prompts.quick_mode import build_quick_mode_prompt
from prompts.deep_mode import build_deep_mode_prompt
from src.data_fetcher import extract_ticker, fetch_financial_data, format_data_for_prompt


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class QuotaExhaustedError(Exception):
    """
    Raised when the Gemini API returns a hard quota limit = 0.
    This is a configuration issue on the Google Cloud project, not a
    transient rate limit — retrying will not help.
    """


# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------
_MAX_RETRIES: int = 3            # maximum attempts before giving up
_RETRY_BASE_DELAY: float = 2.0   # seconds; doubled on each retry (exponential backoff)


# ---------------------------------------------------------------------------
# Scenario re-run trigger keywords
# ---------------------------------------------------------------------------
_SCENARIO_TRIGGERS = [
    "re-evaluate", "reevaluate", "re evaluate", "stress test",
    "assuming", "under inflation", "under recession", "under rate", "scenario",
]


def _is_scenario_rerun(query: str) -> bool:
    normalized = query.lower()
    return any(t in normalized for t in _SCENARIO_TRIGGERS)


def _detect_scenario_focus(query: str) -> str:
    """Extract which scenario(s) the user is requesting re-evaluation for."""
    normalized = query.lower()
    found = []
    scenario_map = {
        "inflation": "High Inflation",
        "rate": "Interest Rate Hike",
        "recession": "Recession",
        "slowdown": "Revenue Slowdown",
        "margin": "Margin Compression",
        "currency": "Currency Depreciation",
        "regulatory": "Regulatory Tightening",
    }
    for token, label in scenario_map.items():
        if token in normalized:
            found.append(label)
    return ", ".join(found) if found else "General Stress Conditions"


def _configure_gemini() -> None:
    """Initialize the Gemini client from config."""
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Please configure it in your .env file."
        )
    genai.configure(api_key=api_key)


def _build_model() -> genai.GenerativeModel:
    """Instantiate the Gemini model with system prompt and generation config."""
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
        generation_config=GENERATION_CONFIG,
    )


def _call_gemini(model: genai.GenerativeModel, user_message: str) -> tuple[str, int, int]:
    """
    Call the Gemini API with automatic exponential backoff retry for transient
    429 rate-limit errors (e.g. RPM exceeded).

    Raises:
        QuotaExhaustedError : when 'limit: 0' is detected — a project-level
                              quota config issue that retrying cannot resolve.
        Exception           : re-raised after exhausting all retries.
    """
    last_error: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = model.generate_content(user_message)
            text = response.text or ""
            usage = getattr(response, "usage_metadata", None)
            if usage:
                prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
            else:
                prompt_tokens = len(user_message) // 4
                completion_tokens = len(text) // 4
            return text, prompt_tokens, completion_tokens
        except Exception as exc:
            error_str = str(exc)
            if "limit: 0" in error_str or "API key expired" in error_str or "API key not valid" in error_str:
                raise QuotaExhaustedError(
                    "Gemini quota issue — switch to Groq by setting GROQ_API_KEY in your .env file."
                ) from exc
            if "429" in error_str and attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                match = re.search(r"retry in ([\d.]+)s", error_str, re.IGNORECASE)
                if match:
                    delay = max(delay, float(match.group(1)))
                time.sleep(delay)
                last_error = exc
                continue
            raise
    raise last_error  # type: ignore[misc]


def _call_groq(user_message: str) -> tuple[str, int, int]:
    """
    Call the Groq API using the OpenAI-compatible chat completions interface.
    Groq's free tier has generous RPM/RPD limits and requires no billing.

    Raises:
        QuotaExhaustedError : on rate limit errors after exhausting retries.
    """
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Please add it to your .env file.\n"
            "Get a free key at: https://console.groq.com"
        )

    client = Groq(api_key=GROQ_API_KEY)
    last_error: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=8192,
                top_p=0.85,
            )
            text = response.choices[0].message.content or ""
            prompt_tokens = response.usage.prompt_tokens if response.usage else len(user_message) // 4
            completion_tokens = response.usage.completion_tokens if response.usage else len(text) // 4
            return text, prompt_tokens, completion_tokens

        except Exception as exc:
            error_str = str(exc)
            if "429" in error_str and attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                match = re.search(r"retry in ([\d.]+)s", error_str, re.IGNORECASE)
                if match:
                    delay = max(delay, float(match.group(1)))
                time.sleep(delay)
                last_error = exc
                continue
            raise

    raise last_error  # type: ignore[misc]


def _call_api(model_or_none: "genai.GenerativeModel | None", user_message: str) -> tuple[str, int, int]:
    """Route API call to Groq or Gemini based on ACTIVE_BACKEND."""
    if ACTIVE_BACKEND == "groq":
        return _call_groq(user_message)
    return _call_gemini(model_or_none, user_message)  # type: ignore[arg-type]


def run_query(
    user_query: str,
    financial_data: dict[str, Any] | None = None,
    skip_clarification: bool = False,
) -> dict[str, Any]:
    """
    Main entry point for processing a research query.

    Parameters:
        user_query        : raw user input string
        financial_data    : optional structured data dict for contradiction detection
        skip_clarification: set True to bypass clarification check (e.g. in tests)

    Returns a dict containing:
        mode              : "QUICK" | "DEEP" | "SCENARIO_RERUN" | "CLARIFICATION"
        formatted_output  : final formatted string ready for display
        raw_response      : raw model text output
        usage             : UsageSummary
        confidence        : ConfidenceResult
        contradictions    : list of contradiction dicts
        memory            : current memory snapshot
        clarification_needed : bool
        clarification_questions : list[str]
    """
    memory = load_memory()

    # ------------------------------------------------------------------
    # 1. Detect if user is updating their preferences
    # ------------------------------------------------------------------
    prefs = extract_preferences_from_input(user_query)
    if prefs:
        for key, val in prefs.items():
            update_preference(key, val)
        memory = load_memory()  # reload updated memory

    # ------------------------------------------------------------------
    # 2. Mode classification
    # ------------------------------------------------------------------
    classification = explain_classification(user_query)
    mode = classification["mode"]

    # ------------------------------------------------------------------
    # 3. Scenario re-run shortcut
    # ------------------------------------------------------------------
    if _is_scenario_rerun(user_query):
        scenario_focus = _detect_scenario_focus(user_query)
        scenario_rows = run_scenarios(scenario_names=[scenario_focus.lower()])
        if not scenario_rows:
            scenario_rows = run_base_downside_stress()

        with Timer() as timer:
            pass  # No API call for scenario re-run — uses engine directly

        usage = estimate_cost(350, 180, latency_ms=timer.elapsed_ms)
        output = format_scenario_only(scenario_rows, usage, trigger=scenario_focus)

        return {
            "mode": "SCENARIO_RERUN",
            "formatted_output": output,
            "raw_response": "",
            "usage": usage,
            "confidence": None,
            "contradictions": [],
            "memory": memory,
            "clarification_needed": False,
            "clarification_questions": [],
        }

    # ------------------------------------------------------------------
    # 4. Clarification check for DEEP MODE
    # ------------------------------------------------------------------
    if not skip_clarification and mode == "DEEP":
        if needs_clarification(user_query, memory, mode):
            questions = get_clarification_questions(memory)
            prompt_text = format_clarification_prompt(questions)
            return {
                "mode": "CLARIFICATION",
                "formatted_output": prompt_text,
                "raw_response": "",
                "usage": estimate_cost(200, 80),
                "confidence": None,
                "contradictions": [],
                "memory": memory,
                "clarification_needed": True,
                "clarification_questions": questions,
            }

    # ------------------------------------------------------------------
    # 5. Fetch real financial data from Yahoo Finance
    # ------------------------------------------------------------------
    ticker = extract_ticker(user_query)
    fetched_data: dict[str, Any] = {}
    data_block: str = ""

    if ticker:
        import warnings as _w
        with _w.catch_warnings():
            _w.simplefilter("ignore")   # silence Pandas4Warning + all yfinance noise
            fetched_data = fetch_financial_data(ticker)
            data_block = format_data_for_prompt(fetched_data)
        # Merge fetched raw metrics into financial_data for contradiction/confidence engine
        financial_data = financial_data or {}
        for key in (
            "revenue_growth_reported", "operating_margin_current",
            "total_debt_current", "net_income_current",
            "free_cash_flow_raw", "source_count", "guidance_verified",
        ):
            if fetched_data.get(key) is not None:
                financial_data[key] = fetched_data[key]
    else:
        financial_data = financial_data or {}

    # ------------------------------------------------------------------
    # 6. Contradiction detection on financial data
    # ------------------------------------------------------------------
    contradictions = detect_contradictions(financial_data)

    # ------------------------------------------------------------------
    # 7. Confidence scoring
    # ------------------------------------------------------------------
    required_fields = [
        "revenue_growth_reported", "operating_margin_current",
        "total_debt_current", "net_income_current",
    ]
    present_count = sum(1 for f in required_fields if financial_data.get(f) is not None)
    data_completeness = present_count / len(required_fields) if required_fields else 1.0

    confidence = calculate_confidence(
        data_completeness=data_completeness,
        contradictions=contradictions,
        source_count=financial_data.get("source_count", 1),
        guidance_verified=financial_data.get("guidance_verified", False),
    )

    # ------------------------------------------------------------------
    # 7. Build prompt and call API (Groq or Gemini)
    # ------------------------------------------------------------------
    if mode == "QUICK":
        user_message = build_quick_mode_prompt(user_query, memory, data_block)
    else:
        user_message = build_deep_mode_prompt(user_query, memory, data_block)

    # Only initialise Gemini model if it is the active backend
    gemini_model = None
    if ACTIVE_BACKEND == "gemini":
        _configure_gemini()
        gemini_model = _build_model()

    with Timer() as timer:
        raw_response, prompt_tokens, completion_tokens = _call_api(gemini_model, user_message)

    # ------------------------------------------------------------------
    # 8. Cost tracking
    # ------------------------------------------------------------------
    usage = estimate_cost(prompt_tokens, completion_tokens, latency_ms=timer.elapsed_ms)

    # ------------------------------------------------------------------
    # 9. Format output
    # ------------------------------------------------------------------
    if mode == "QUICK":
        formatted_output = format_quick_mode(
            model_response=raw_response,
            cost_summary=usage,
            confidence_result=confidence,
            contradictions=contradictions,
        )
    else:
        # For Deep Mode, parse the model's response into sections (best-effort)
        # The model is instructed to use # N. headers — we pass raw_response as executive_summary
        # and let format_deep_mode render the structural wrapper
        scenario_rows = run_base_downside_stress(financial_data)
        sections = {
            "executive_summary": raw_response,  # full response embedded in section 1 area
        }
        formatted_output = format_deep_mode(
            sections=sections,
            scenario_rows=scenario_rows,
            confidence_result=confidence,
            cost_summary=usage,
            contradictions=contradictions,
        )

    # ------------------------------------------------------------------
    # 10. Update memory with analyzed company if extracted
    # ------------------------------------------------------------------
    _extract_and_store_company(user_query)

    return {
        "mode": mode,
        "formatted_output": formatted_output,
        "raw_response": raw_response,
        "usage": usage,
        "confidence": confidence,
        "contradictions": contradictions,
        "memory": load_memory(),
        "clarification_needed": False,
        "clarification_questions": [],
    }


def _extract_and_store_company(query: str) -> None:
    """
    Best-effort extraction of company name from query for memory storage.
    Looks for quoted names or common financial tickers.
    """
    import re
    # Match words in quotes or known tickers (3-5 uppercase letters)
    quoted = re.findall(r'"([^"]+)"', query)
    tickers = re.findall(r'\b([A-Z]{2,5})\b', query)
    companies = quoted + [t for t in tickers if t not in {"YOY", "KPI", "FCF", "ROE", "DCF", "EPS"}]
    for company in companies[:2]:
        try:
            update_preference("previously_analyzed", company)
        except Exception:
            pass
