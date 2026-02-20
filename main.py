"""
main.py
FIN-SIGHT – Interactive CLI entry point.
Runs an interactive research session with persistent memory and structured output.
"""

from __future__ import annotations
import sys
import os
import warnings

# Suppress noisy third-party deprecation warnings before any imports
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*utcnow.*")
warnings.filterwarnings("ignore", message=".*google.generativeai.*")

# Ensure project root is on the path when running as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table as RichTable

from src.agent import run_query, QuotaExhaustedError
from src.memory import load_memory, memory_summary, reset_memory

console = Console()

_BANNER = """
FIN-SIGHT  |  Financial & Market Deep Research Agent
Explain. Compare. Justify.
"""

_HELP_TEXT = """
Available commands:
  /memory        — Display current stored user profile
  /reset-memory  — Clear all stored preferences
  /help          — Show this help message
  /quit or /exit — Exit the session

Query types:
  QUICK MODE  — Earnings summaries, single KPI lookups, snapshots
  DEEP MODE   — Comparisons, bull/bear analysis, scenario analysis, valuation

To store preferences, state them directly:
  Example: "I am conservative. I prefer ROE and FCF. 5-year horizon."
"""

_DIVIDER = "-" * 72


def _print_banner() -> None:
    console.print(Panel(Text(_BANNER.strip(), justify="center"), border_style="dim white"))
    console.print()


def _print_divider() -> None:
    console.print(_DIVIDER, style="dim")


def _handle_command(command: str) -> bool:
    """
    Handle slash commands. Returns True if the loop should continue, False to exit.
    """
    cmd = command.strip().lower()

    if cmd in ("/quit", "/exit"):
        console.print("\nSession terminated.", style="dim")
        return False

    if cmd == "/help":
        console.print(_HELP_TEXT)
        return True

    if cmd == "/memory":
        mem = load_memory()
        console.print()
        console.print(memory_summary(mem))
        console.print()
        return True

    if cmd == "/reset-memory":
        reset_memory()
        console.print("Memory reset to defaults.", style="yellow")
        return True

    console.print(f"Unknown command: {command}. Type /help for available commands.", style="yellow")
    return True


def _print_deep_mode(result: dict) -> None:
    """Render a Deep Mode result using Rich components for maximum readability."""
    from datetime import datetime, timezone

    # --- Header (full-width, centred) ---
    console.print(
        Panel(
            Text(
                f"FIN-SIGHT  |  INVESTMENT RESEARCH MEMO  |  DEEP MODE\n"
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                justify="center",
                style="bold white",
            ),
            border_style="cyan",
            expand=True,
        )
    )
    console.print()

    # --- Model body (Markdown renders bold, tables, headings) ---
    raw = result.get("raw_response", "").strip()
    if raw:
        console.print(Markdown(raw))
    console.print()

    # --- Contradiction Check ---
    console.print(Rule(" CONTRADICTION CHECK ", style="yellow"))
    contradictions = result.get("contradictions", []) or []
    if contradictions:
        console.print("[bold red]WARNING: Contradictions Detected[/bold red]")
        for c in contradictions:
            console.print(f"  [red]•[/red] {c.get('description', str(c))}")
    else:
        console.print("[green]✓  No contradictions detected.[/green]")
    console.print()

    # --- Confidence ---
    console.print(Rule(" CONFIDENCE & UNCERTAINTY ", style="blue"))
    confidence = result.get("confidence")
    if confidence:
        score = getattr(confidence, "score", 0.0)
        grade = getattr(confidence, "grade", "N/A")
        rationale = getattr(confidence, "rationale", "")
        color = "green" if grade == "HIGH" else "yellow" if grade == "MEDIUM" else "red"
        console.print(f"Confidence Score  : [{color}][bold]{score:.2f} / 1.00  [{grade}][/bold][/{color}]")
        for line in (rationale or "").strip().split("\n"):
            if line.strip():
                console.print(f"  [dim]{line.strip()}[/dim]")
    console.print()

    # --- Token Usage & Cost ---
    _print_cost_table(result.get("usage"))


def _print_quick_mode(result: dict) -> None:
    """Render a Quick Mode result with styled bullets and cyan numbers."""
    import re

    # Regex: matches currency ($1.23B), percentages (6.1%), plain decimals, ranges
    _NUM_RE = re.compile(
        r"(\$[\d,.]+[BMTKk]?(?:\s*[–\-]\s*\$?[\d,.]+[BMTKk]?)?"
        r"|[\d,.]+%"
        r"|\b[\d]+\.\d+\b"
        r"|\b[\d]{1,3}(?:,[\d]{3})+\b)"
    )

    def _colorize(text: str) -> str:
        """Wrap numbers in cyan Rich markup."""
        return _NUM_RE.sub(r"[cyan]\1[/cyan]", text)

    # Header
    console.print(Rule(" FIN-SIGHT  |  QUICK MODE SUMMARY ", style="cyan"))
    console.print()

    raw = result.get("raw_response", "").strip()
    in_summary = False

    for line in raw.split("\n"):
        stripped = line.strip()

        if not stripped:
            console.print()
            in_summary = False
            continue

        # Bullet line: "• **Field:** value" or "- **Field:** value"
        bullet_match = re.match(r"^[•\-\*]\s*\*\*(.+?)\*\*:?\s*(.*)", stripped)
        if bullet_match:
            field = bullet_match.group(1).rstrip(":")
            value = bullet_match.group(2)
            colored_value = _colorize(value)
            console.print(f"  [bold white]{field}:[/bold white] {colored_value}")
            in_summary = False
        else:
            # Summary paragraph or other text — render dim-italic
            console.print(f"[dim italic]{_colorize(stripped)}[/dim italic]")
            in_summary = True

    console.print()

    # Contradiction
    contradictions = result.get("contradictions", []) or []
    if contradictions:
        console.print(Rule(" CONTRADICTION ALERT ", style="red"))
        for c in contradictions:
            console.print(f"  [red]•[/red] {c.get('description', str(c))}")
        console.print()

    # Confidence
    console.print(Rule(" CONFIDENCE ", style="blue"))
    confidence = result.get("confidence")
    if confidence:
        score = getattr(confidence, "score", 0.0)
        grade = getattr(confidence, "grade", "N/A")
        color = "green" if grade == "HIGH" else "yellow" if grade == "MEDIUM" else "red"
        console.print(f"  Score: [{color}][bold]{score:.2f} / 1.00  [{grade}][/bold][/{color}]")
    console.print()

    # Cost
    _print_cost_table(result.get("usage"))


def _print_cost_table(usage) -> None:
    """Render a clean token usage & cost table."""
    console.print(Rule(" TOKEN USAGE & COST ", style="dim"))
    if usage:
        t = RichTable(show_header=False, box=None, padding=(0, 2))
        t.add_column(style="dim", min_width=22)
        t.add_column(style="bold white")
        t.add_row("Prompt Tokens",     f"{usage.prompt_tokens:,}")
        t.add_row("Completion Tokens", f"{usage.completion_tokens:,}")
        t.add_row("Total Tokens",      f"{usage.total_tokens:,}")
        t.add_row("Estimated Cost",    f"[green]${usage.estimated_cost_usd:.6f} USD[/green]")
        t.add_row("Model",             f"[cyan]{usage.model}[/cyan]")
        t.add_row("Latency",           f"{usage.latency_ms} ms")
        console.print(t)
    console.print()


def _run_session() -> None:
    """Main interactive loop."""
    _print_banner()
    console.print(
        "Type your research query below. For guidance, type /help. To exit, type /quit.",
        style="dim"
    )
    console.print()

    pending_clarification = False
    last_query = ""

    while True:
        try:
            user_input = console.input("[bold white]FIN-SIGHT > [/bold white]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\nSession terminated.", style="dim")
            break

        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            should_continue = _handle_command(user_input)
            if not should_continue:
                break
            continue

        # If we were waiting for clarification answers, combine with last query
        query = user_input
        skip_clarification = False
        if pending_clarification:
            query = f"{last_query} | User clarification: {user_input}"
            skip_clarification = True
            pending_clarification = False

        console.print()
        console.print("Processing...", style="dim italic")
        console.print()

        try:
            result = run_query(query, skip_clarification=skip_clarification)
        except EnvironmentError as e:
            console.print(f"\n[ERROR] Configuration issue: {e}", style="bold red")
            console.print(
                "Please set GROQ_API_KEY in your .env file and restart.",
                style="yellow"
            )
            break
        except QuotaExhaustedError as e:
            console.print("\nQUOTA / API ERROR", style="bold red")
            console.print(str(e), style="yellow")
            console.print("\nThe session will remain open. Fix the quota issue and retry.", style="dim")
            continue
        except Exception as e:
            console.print(f"\n[ERROR] An unexpected error occurred: {e}", style="bold red")
            console.print("Please review your query and try again.", style="dim")
            continue

        mode = result.get("mode", "UNKNOWN")
        output = result.get("formatted_output", "")

        # Display mode label
        mode_labels = {
            "QUICK": "QUICK MODE",
            "DEEP": "DEEP MODE",
            "SCENARIO_RERUN": "SCENARIO RE-RUN",
            "CLARIFICATION": "CLARIFICATION REQUIRED",
        }
        label = mode_labels.get(mode, mode)
        console.print(Rule(f" {label} ", style="dim white"))
        console.print()

        # Print output
        if mode == "DEEP":
            _print_deep_mode(result)
        elif mode in ("QUICK", "SCENARIO_RERUN"):
            _print_quick_mode(result)
        else:
            console.print(output)
        console.print()

        # Handle clarification mode
        if mode == "CLARIFICATION":
            pending_clarification = True
            last_query = user_input
            console.print("Please answer the above questions to proceed with the analysis.", style="dim italic")
        else:
            pending_clarification = False

        console.print()


if __name__ == "__main__":
    _run_session()
