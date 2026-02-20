"""
src/memory.py
FIN-SIGHT – Persistent financial memory module.
Stores and retrieves user preferences across sessions using a local JSON file.
"""

import json
import os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Memory file path — sibling to src/ inside the project root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE: Path = _PROJECT_ROOT / "data" / "memory.json"

_DEFAULT_MEMORY: dict[str, Any] = {
    "risk_tolerance": None,        # Conservative | Moderate | Aggressive
    "preferred_kpis": [],          # e.g. ["EBITDA", "ROE", "FCF"]
    "preferred_sectors": [],       # e.g. ["Technology", "Healthcare"]
    "geographic_focus": [],        # e.g. ["US", "India", "Europe"]
    "time_horizon": None,          # e.g. "5 years", "Short-term"
    "previously_analyzed": [],     # list of company names / tickers
}


def _ensure_file() -> None:
    """Create the memory file with defaults if it does not exist."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        with open(MEMORY_FILE, "w", encoding="utf-8") as fh:
            json.dump(_DEFAULT_MEMORY, fh, indent=2)


def load_memory() -> dict[str, Any]:
    """Load the persistent memory store. Returns defaults if file is absent or corrupt."""
    _ensure_file()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        # Back-fill any missing keys added in future versions
        for key, default in _DEFAULT_MEMORY.items():
            data.setdefault(key, default)
        return data
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_MEMORY)


def save_memory(data: dict[str, Any]) -> None:
    """Persist updated memory to disk."""
    _ensure_file()
    with open(MEMORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def update_preference(key: str, value: Any) -> dict[str, Any]:
    """
    Update a single memory key and persist.

    For list-valued keys (preferred_kpis, preferred_sectors, geographic_focus,
    previously_analyzed), value may be a single item or a list — it is appended
    without duplicates.

    Returns the updated memory dict.
    """
    if key not in _DEFAULT_MEMORY:
        raise ValueError(f"Unknown memory key: '{key}'. Valid keys: {list(_DEFAULT_MEMORY)}")

    data = load_memory()
    existing = data.get(key)

    if isinstance(existing, list):
        items = value if isinstance(value, list) else [value]
        for item in items:
            if item not in existing:
                existing.append(item)
        data[key] = existing
    else:
        data[key] = value

    save_memory(data)
    return data


def get_memory() -> dict[str, Any]:
    """Convenience alias for load_memory."""
    return load_memory()


def reset_memory() -> None:
    """Reset memory to defaults. Use with care — for testing only."""
    save_memory(dict(_DEFAULT_MEMORY))


def memory_summary(data: dict[str, Any]) -> str:
    """Return a compact human-readable summary of current memory state."""
    lines = ["Stored User Profile:"]
    lines.append(f"  Risk Tolerance     : {data.get('risk_tolerance') or 'Not set'}")
    lines.append(f"  Preferred KPIs     : {', '.join(data.get('preferred_kpis') or []) or 'Not set'}")
    lines.append(f"  Preferred Sectors  : {', '.join(data.get('preferred_sectors') or []) or 'Not set'}")
    lines.append(f"  Geographic Focus   : {', '.join(data.get('geographic_focus') or []) or 'Not set'}")
    lines.append(f"  Time Horizon       : {data.get('time_horizon') or 'Not set'}")
    analyzed = data.get("previously_analyzed") or []
    lines.append(f"  Previously Analyzed: {', '.join(analyzed[-5:]) or 'None'}")
    return "\n".join(lines)
