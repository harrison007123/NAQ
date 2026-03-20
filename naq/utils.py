"""
utils.py — Shared utility functions for NAQ.
"""

from typing import Optional
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


# ── Rich Table Renderer ───────────────────────────────────────────────────────

def render_dataframe(df: pd.DataFrame, title: Optional[str] = None, max_rows: int = 200) -> None:
    """
    Render a pandas DataFrame as a styled Rich table in the terminal.
    """
    if df.empty:
        console.print("  [dim italic]No results returned.[/dim italic]")
        return

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