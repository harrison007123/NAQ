"""
utils.py — Shared utility functions for NAQ.

Includes:
  - Query history management
  - Rich table renderer for DataFrames
  - Miscellaneous helpers
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

HISTORY_FILE = Path.home() / ".naq" / "history.json"
MAX_HISTORY_ENTRIES = 500


# ── History ───────────────────────────────────────────────────────────────────


def _load_history_raw() -> List[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_history_raw(entries: List[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries[-MAX_HISTORY_ENTRIES:], f, indent=2, ensure_ascii=False)


def add_to_history(question: str, sql: str) -> None:
    """Save a query pair to history."""
    entries = _load_history_raw()
    entries.append(
        {
            "ts": datetime.utcnow().isoformat(),
            "question": question,
            "sql": sql,
        }
    )
    _save_history_raw(entries)


def get_history(limit: int = 20) -> List[dict]:
    """Return the most recent *limit* history entries (newest first)."""
    entries = _load_history_raw()
    return list(reversed(entries[-limit:]))


def clear_history() -> None:
    """Delete all saved history."""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


# ── Rich Table Renderer ───────────────────────────────────────────────────────


def render_dataframe(df: pd.DataFrame, title: Optional[str] = None, max_rows: int = 200) -> None:
    """
    Render a pandas DataFrame as a styled Rich table in the terminal.
    """
    if df.empty:
        console.print("  [dim italic]No results returned.[/dim italic]")
        return

    # Truncate very large results
    truncated = len(df) > max_rows
    display_df = df.head(max_rows)

    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        show_lines=True,
        highlight=True,
    )

    for col in display_df.columns:
        table.add_column(str(col), overflow="fold")

    for _, row in display_df.iterrows():
        table.add_row(*[str(v) if v is not None else "[dim]NULL[/dim]" for v in row])

    console.print()
    console.print(table)

    row_label = "row" if len(df) == 1 else "rows"
    if truncated:
        console.print(
            f"  [dim]Showing {max_rows} of {len(df)} {row_label}. "
            "Add a LIMIT clause to narrow results.[/dim]"
        )
    else:
        console.print(f"  [dim]{len(df)} {row_label} returned.[/dim]")
    console.print()


# ── Schema Pretty-Printer ─────────────────────────────────────────────────────


def print_schema(schema: dict) -> None:
    """Print the database schema as a rich table."""
    if not schema:
        console.print("  [dim]No tables found in the database.[/dim]")
        return

    for table_name, info in schema.items():
        table = Table(
            title=f"[bold cyan]{table_name}[/bold cyan]",
            box=box.SIMPLE_HEAVY,
            border_style="bright_black",
            header_style="bold yellow",
            show_lines=False,
        )
        table.add_column("Column", style="white")
        table.add_column("Type", style="cyan")
        table.add_column("PK", justify="center")
        table.add_column("Nullable", justify="center")

        for col in info["columns"]:
            table.add_row(
                col["name"],
                col["type"],
                "✓" if col.get("pk") else "",
                "" if col.get("nullable", True) else "NOT NULL",
            )

        console.print(table)

        if info.get("foreign_keys"):
            for fk in info["foreign_keys"]:
                console.print(
                    f"  [dim]  FK: {table_name}.{fk['column']} → {fk['ref_table']}.{fk['ref_col']}[/dim]"
                )
        console.print()


# ── Misc ──────────────────────────────────────────────────────────────────────


def truncate_string(s: str, max_len: int = 80) -> str:
    return s if len(s) <= max_len else s[: max_len - 3] + "…"
