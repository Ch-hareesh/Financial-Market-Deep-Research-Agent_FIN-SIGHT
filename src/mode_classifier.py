"""
src/mode_classifier.py
FIN-SIGHT – Dual research mode classifier.
Determines whether a user query should be routed to QUICK MODE or DEEP MODE
based on keyword signals, query length, and structural cues.
"""

from __future__ import annotations
from typing import Literal

from src.config import (
    DEEP_MODE_KEYWORDS,
    QUICK_MODE_KEYWORDS,
    QUICK_MODE_MAX_QUERY_WORDS,
)

ResearchMode = Literal["QUICK", "DEEP"]


def classify_mode(query: str) -> ResearchMode:
    """
    Classify a user query as QUICK or DEEP mode.

    Rules (in priority order):
    1. If any DEEP keyword is found → DEEP
    2. If any QUICK keyword is found AND word count <= threshold → QUICK
    3. If word count <= threshold with no DEEP signals → QUICK
    4. Default to DEEP for ambiguous or long queries

    Returns:
        "QUICK" or "DEEP"
    """
    if not query or not query.strip():
        return "QUICK"

    normalized = query.lower().strip()
    words = normalized.split()
    word_count = len(words)

    # --- Priority 1: Explicit DEEP signals ---
    for keyword in DEEP_MODE_KEYWORDS:
        if keyword in normalized:
            return "DEEP"

    # --- Priority 2: Explicit QUICK signals ---
    for keyword in QUICK_MODE_KEYWORDS:
        if keyword in normalized:
            return "QUICK"

    # --- Priority 3: Length-based heuristic ---
    if word_count <= QUICK_MODE_MAX_QUERY_WORDS:
        return "QUICK"

    # --- Default: Long or ambiguous → treat as DEEP ---
    return "DEEP"


def explain_classification(query: str) -> dict[str, object]:
    """
    Return a dict including the classified mode and the triggering reason.
    Useful for logging and transparency.
    """
    normalized = query.lower().strip()
    words = normalized.split()
    word_count = len(words)

    for keyword in DEEP_MODE_KEYWORDS:
        if keyword in normalized:
            return {
                "mode": "DEEP",
                "reason": f"DEEP keyword detected: '{keyword}'",
                "query_word_count": word_count,
            }

    for keyword in QUICK_MODE_KEYWORDS:
        if keyword in normalized:
            return {
                "mode": "QUICK",
                "reason": f"QUICK keyword detected: '{keyword}'",
                "query_word_count": word_count,
            }

    if word_count <= QUICK_MODE_MAX_QUERY_WORDS:
        return {
            "mode": "QUICK",
            "reason": f"Short query ({word_count} words, threshold: {QUICK_MODE_MAX_QUERY_WORDS})",
            "query_word_count": word_count,
        }

    return {
        "mode": "DEEP",
        "reason": f"Long query ({word_count} words) with no QUICK signals",
        "query_word_count": word_count,
    }
