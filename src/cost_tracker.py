"""
src/cost_tracker.py
FIN-SIGHT – Token usage and cost reporting module.
Tracks prompt and completion tokens, estimates USD cost from the pricing table,
and returns a structured usage summary for every response.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any

from src.config import PRICING_TABLE, MODEL_NAME, GROQ_MODEL_NAME, ACTIVE_BACKEND

# Resolve the model name that is actually being used for this session
_ACTIVE_MODEL: str = GROQ_MODEL_NAME if ACTIVE_BACKEND == "groq" else MODEL_NAME


@dataclass
class UsageSummary:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model: str
    latency_ms: int

    def format(self) -> str:
        """Return the mandatory token/cost block for embedding in responses."""
        return (
            f"Prompt Tokens      : {self.prompt_tokens:,}\n"
            f"Completion Tokens  : {self.completion_tokens:,}\n"
            f"Total Tokens       : {self.total_tokens:,}\n"
            f"Estimated Cost     : ${self.estimated_cost_usd:.6f} USD\n"
            f"Model              : {self.model}\n"
            f"Latency            : {self.latency_ms} ms"
        )


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str | None = None,
    latency_ms: int = 0,
) -> UsageSummary:
    """
    Compute cost from token counts using the pricing table.

    Parameters:
        prompt_tokens     : number of input tokens consumed
        completion_tokens : number of output tokens generated
        model             : model name (defaults to config MODEL_NAME)
        latency_ms        : measured latency in milliseconds

    Returns:
        UsageSummary dataclass
    """
    model = model or _ACTIVE_MODEL
    pricing = PRICING_TABLE.get(model, PRICING_TABLE["default"])

    input_cost = (prompt_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (completion_tokens / 1000) * pricing["output_per_1k"]
    total_cost = round(input_cost + output_cost, 8)

    return UsageSummary(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost_usd=total_cost,
        model=model,
        latency_ms=latency_ms,
    )


def estimate_quick_mode_cost(completion_tokens: int = 300, latency_ms: int = 0) -> UsageSummary:
    """Convenience estimate for Quick Mode with assumed system prompt size."""
    return estimate_cost(
        prompt_tokens=1200,   # system prompt + user query estimate
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
    )


def estimate_deep_mode_cost(completion_tokens: int = 2500, latency_ms: int = 0) -> UsageSummary:
    """Convenience estimate for Deep Mode with assumed system prompt size."""
    return estimate_cost(
        prompt_tokens=2500,   # system prompt + memory + user query estimate
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
    )


class Timer:
    """Simple wall-clock timer for measuring API call latency."""

    def __init__(self) -> None:
        self._start: float = 0.0
        self._end: float = 0.0

    def start(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def stop(self) -> "Timer":
        self._end = time.perf_counter()
        return self

    @property
    def elapsed_ms(self) -> int:
        return int((self._end - self._start) * 1000)

    def __enter__(self) -> "Timer":
        return self.start()

    def __exit__(self, *_: Any) -> None:
        self.stop()
