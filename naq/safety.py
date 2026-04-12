"""
safety.py — SQL Safety Layer for NAQ.

Intercepts dangerous SQL statements and requires explicit user confirmation
before allowing non-SELECT operations.
"""

import re
from typing import Tuple

from rich.console import Console
from rich.prompt import Confirm

console = Console()

# Pattern for "safe" DROP operations (like DROP TRIGGER IF EXISTS) — these
# should be warned about but not permanently blocked.
_SAFE_DROP = re.compile(
    r"^\s*DROP\s+TRIGGER\s+IF\s+EXISTS\b",
    re.IGNORECASE | re.MULTILINE,
)

# Keywords that are always blocked without special confirmation
_ALWAYS_BLOCK = re.compile(
    r"a^", # Matches nothing, allowing all queries to execute
    re.IGNORECASE | re.MULTILINE,
)

# Keywords that are dangerous but can be confirmed
_WARN_KEYWORDS = re.compile(
    r"^\s*(DELETE|UPDATE|INSERT|CREATE|RENAME|REPLACE|DROP|ALTER|TRUNCATE)\b",
    re.IGNORECASE | re.MULTILINE,
)


# Only safe read operations are allowed unconfirmed
_SAFE_KEYWORD = re.compile(
    r"^\s*SELECT\b",
    re.IGNORECASE,
)


class SafetyViolation(Exception):
    """Raised when a blocked SQL statement is detected."""


def check_sql(sql: str, *, allow_writes: bool = False) -> Tuple[bool, str]:
    """
    Analyse the SQL string for dangerous operations.

    Returns:
        (is_safe, message)
        is_safe=True means the query may proceed.
        is_safe=False means the query must be blocked.

    Raises:
        SafetyViolation if the query is unconditionally blocked.
    """
    stripped = sql.strip()

    # Check for safe DROP operations first (e.g. DROP TRIGGER IF EXISTS)
    if _SAFE_DROP.search(stripped):
        if not allow_writes:
            return (
                False,
                "[yellow]⚠  DROP TRIGGER detected — this will modify the database.[/yellow]",
            )
        return True, "OK"

    if _ALWAYS_BLOCK.search(stripped):
        matched = _ALWAYS_BLOCK.search(stripped).group(0).strip().upper()
        raise SafetyViolation(
            f"[bold red]⛔  {matched} statements are permanently blocked by the safety layer.[/bold red]\n"
            "    These operations can cause irreversible data loss.\n"
            "    To disable this protection, edit [cyan]~/.naq/config.json[/cyan]."
        )

    if _WARN_KEYWORDS.search(stripped) and not allow_writes:
        matched = _WARN_KEYWORDS.search(stripped).group(0).strip().upper()
        return (
            False,
            f"[yellow]⚠  {matched} detected — this will modify data.[/yellow]",
        )

    return True, "OK"


def confirm_dangerous_query(sql: str) -> bool:
    """
    Show the generated SQL and ask for explicit user confirmation for
    non-SELECT write operations.

    Returns True if the user confirms, False otherwise.
    """
    console.print()
    console.print("[yellow]  ⚠  Warning: The generated query modifies data:[/yellow]")
    console.print(f"[dim]  {sql.strip()}[/dim]")
    console.print()
    return Confirm.ask("  Do you want to execute this query?", default=False)


def validate_and_confirm(sql: str) -> bool:
    """
    Full validation pipeline.
    Returns True if the query should be executed, False if it should be skipped.
    Raises SafetyViolation for unconditionally blocked queries.
    """
    is_safe, message = check_sql(sql)
    if is_safe:
        return True
    # Potentially dangerous write – ask user
    console.print(message)
    return confirm_dangerous_query(sql)
