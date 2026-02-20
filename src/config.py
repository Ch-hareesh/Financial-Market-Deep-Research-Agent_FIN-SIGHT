"""
src/config.py
FIN-SIGHT – Configuration module.
Loads environment variables and defines model constants, pricing tables, and thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly target the project root .env — never reads from Downloads or
# any other ambient location. override=True ensures a fresh load every run.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DOTENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)


# ---------------------------------------------------------------------------
# Primary backend: Groq (free tier, no billing required)
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_NAME: str = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

# ---------------------------------------------------------------------------
# Fallback backend: Gemini (optional)
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.0-flash")

# Active backend: prefers Groq if key is set, else falls back to Gemini
ACTIVE_BACKEND: str = "groq" if GROQ_API_KEY else "gemini"

# ---------------------------------------------------------------------------
# Token pricing table (USD per 1,000 tokens)
# Values are approximate and subject to Google's published pricing.
# ---------------------------------------------------------------------------
PRICING_TABLE: dict[str, dict[str, float]] = {
    # Groq free-tier models ($0.00 on free tier)
    "llama-3.3-70b-versatile": {
        "input_per_1k": 0.0000590,  # $0.059 / 1M tokens (paid tier reference)
        "output_per_1k": 0.0000790,
    },
    "llama-3.1-8b-instant": {
        "input_per_1k": 0.0000050,
        "output_per_1k": 0.0000080,
    },
    "mixtral-8x7b-32768": {
        "input_per_1k": 0.0000240,
        "output_per_1k": 0.0000240,
    },
    "gemma2-9b-it": {
        "input_per_1k": 0.0000200,
        "output_per_1k": 0.0000200,
    },
    # Gemini models
    "gemini-2.5-pro-exp-03-25": {
        "input_per_1k": 0.00125,
        "output_per_1k": 0.01000,
    },
    "gemini-2.0-flash": {
        "input_per_1k": 0.000075,
        "output_per_1k": 0.000300,
    },
    "gemini-1.5-pro": {
        "input_per_1k": 0.00125,
        "output_per_1k": 0.00500,
    },
    "default": {
        "input_per_1k": 0.000059,
        "output_per_1k": 0.000079,
    },
}

# ---------------------------------------------------------------------------
# Generation parameters
# ---------------------------------------------------------------------------
GENERATION_CONFIG: dict[str, object] = {
    "temperature": 0.3,        # Low temperature for deterministic, analytical output
    "top_p": 0.85,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# ---------------------------------------------------------------------------
# Mode thresholds
# ---------------------------------------------------------------------------
QUICK_MODE_MAX_QUERY_WORDS: int = 25   # Queries under this word count lean toward QUICK
DEEP_MODE_KEYWORDS: list[str] = [
    "compare", "comparison", "vs", "versus", "bull", "bear",
    "scenario", "sensitivity", "stress", "valuation", "dcf",
    "breakdown", "fundamental", "full analysis", "deep dive",
    "peer", "benchmarking", "forecast", "model", "investment thesis",
]

QUICK_MODE_KEYWORDS: list[str] = [
    "summarize", "summary", "recap", "what is", "what was",
    "revenue", "earnings", "eps", "quick", "snapshot", "top line",
    "highlight", "brief", "kpi",
]
