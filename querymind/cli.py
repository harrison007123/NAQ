import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

from querymind import __version__
from querymind.banner import print_banner, animated_startup, thinking_steps
from querymind.config import prompt_for_config
from querymind import db as database
from querymind import schema_loader
from querymind import ai_engine
from querymind import executor
from querymind import safety
from querymind import utils

app = typer.Typer(
    name="querymind",
    help="QueryMind 3 — AI Natural Language → SQL Engine",
    add_completion=False,
)

console = Console()

PROMPT_STYLE = Style.from_dict({"prompt": "bold ansicyan"})

HISTORY_PATH = Path.home() / ".querymind" / "prompt_history"

HELP_TEXT = """
[bold cyan]Commands[/bold cyan]

  [bold green]help[/bold green]           Show this help
  [bold green]schema[/bold green]         Display database schema
  [bold green]schema refresh[/bold green] Reload schema from database
  [bold green]history[/bold green]        Recent query history
  [bold green]history clear[/bold green]  Clear history
  [bold green]config[/bold green]         Re-enter credentials
  [bold green]exit[/bold green]           Exit QueryMind 3

[bold cyan]Natural Language Queries[/bold cyan]

  [dim]QueryMind > show top 10 customers by revenue[/dim]
  [dim]QueryMind > how many orders placed last month?[/dim]
  [dim]QueryMind > list products with stock below 20[/dim]

[dim]─────────────────────────────────────────────────[/dim]
  Developed by [bold magenta]Harrison Bennett J[/bold magenta]  ·  [dim]QueryMind v3.0.0[/dim]
"""


def _handle_command(command: str, cfg: dict, conn) -> bool:
    cmd = command.strip().lower()

    if cmd in ("exit", "quit", "q"):
        console.print()
        console.print(Rule(style="bright_black"))
        console.print("  [bold cyan]Goodbye! 👋  QueryMind session ended.[/bold cyan]")
        console.print(Rule(style="bright_black"))
        console.print()
        database.disconnect()
        raise SystemExit(0)

    if cmd == "help":
        console.print(
            Panel(HELP_TEXT, border_style="cyan", title="[bold]QueryMind Help[/bold]",
                  box=__import__("rich.box", fromlist=["ROUNDED"]).ROUNDED, padding=(1, 2))
        )
        return True

    if cmd == "schema":
        console.print()
        console.print(Rule("[bold cyan]  Database Schema  [/bold cyan]", style="cyan"))
        schema = schema_loader.fetch_schema(conn, cfg)
        utils.print_schema(schema)
        return True

    if cmd == "schema refresh":
        schema_loader.clear_cache()
        schema_loader.fetch_schema(conn, cfg, force_refresh=True)
        console.print("  [bold green]✓[/bold green] Schema cache refreshed.")
        return True

    if cmd == "history":
        entries = utils.get_history(limit=20)
        if not entries:
            console.print("  [dim]No history yet.[/dim]")
            return True
        console.print()
        console.print(Rule("[bold cyan]  Query History  [/bold cyan]", style="cyan"))
        for i, entry in enumerate(entries, 1):
            ts = entry.get("ts", "")[:19].replace("T", " ")
            q = utils.truncate_string(entry.get("question", ""), 60)
            sql_short = utils.truncate_string(entry.get("sql", ""), 80)
            console.print(f"  [dim]{i:2}. [{ts}][/dim] [white]{q}[/white]")
            console.print(f"  [dim]      SQL: {sql_short}[/dim]")
        console.print()
        return True

    if cmd == "history clear":
        utils.clear_history()
        console.print("  [bold green]✓[/bold green] History cleared.")
        return True

    if cmd == "config":
        console.print()
        console.print(Rule("[bold yellow]  Re-entering Credentials  [/bold yellow]", style="yellow"))
        new_cfg = prompt_for_config()
        try:
            database.disconnect()
            new_conn = database.connect(new_cfg)
            schema_loader.clear_cache()
            schema_loader.fetch_schema(new_conn, new_cfg)
            console.print("  [bold green]✓[/bold green] Reconnected with new credentials.")
        except Exception as exc:
            console.print(f"  [bold red]✗[/bold red] Could not connect: {exc}")
        return True

    return False


def _run_nl_query(question: str, cfg: dict, conn, schema_text: str) -> None:
    try:
        console.print()
        console.print(Rule(style="bright_black"))

        thinking_steps([
            "Analyzing schema...",
            "Generating SQL query...",
        ])

        sql = ai_engine.generate_sql(cfg, schema_text, question)
        if not sql:
            console.print("  [yellow]⚠  The LLM returned an empty response. Please rephrase.[/yellow]")
            return

        console.print(
            Panel(
                Syntax(sql, "sql", theme="monokai", line_numbers=False, word_wrap=True),
                title="[bold dim]Generated SQL[/bold dim]",
                border_style="bright_black",
                padding=(0, 1),
            )
        )
        console.print()

        try:
            should_proceed = safety.validate_and_confirm(sql)
        except safety.SafetyViolation as exc:
            console.print(f"\n  {exc}\n")
            return

        if not should_proceed:
            console.print("  [dim]Query cancelled.[/dim]")
            return

        thinking_steps(["Executing query..."])

        result = executor.execute_query(conn, sql)

        utils.render_dataframe(result.df, title=f"Results — {question[:60]}")

        utils.add_to_history(question, sql)

        console.print(Rule(style="bright_black"))

    except RuntimeError as exc:
        console.print(f"\n  [bold red]✗ Error:[/bold red] {exc}\n")
        console.print(Rule(style="red"))
    except Exception as exc:
        console.print(f"\n  [bold red]✗ Unexpected error:[/bold red] {exc}\n")
        console.print(Rule(style="red"))


def _main_loop(cfg: dict, conn) -> None:
    animated_startup([
        "Connecting to database",
        "Loading database schema",
        "Initializing AI engine",
        "QueryMind ready",
    ])

    schema = schema_loader.fetch_schema(conn, cfg)
    schema_text = schema_loader.schema_to_text(conn, cfg)
    table_count = len(schema)

    console.print(
        Panel(
            f"  [bold green]✓[/bold green]  Connected to [bold cyan]{cfg['database']['name']}[/bold cyan]  "
            f"·  [bold green]{table_count}[/bold green] table(s) loaded  "
            f"·  LLM: [bold magenta]{cfg['llm']['provider'].capitalize()} / {cfg['llm']['model']}[/bold magenta]",
            border_style="green",
            padding=(0, 1),
        )
    )
    console.print()

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    session: PromptSession = PromptSession(
        history=FileHistory(str(HISTORY_PATH)),
        auto_suggest=AutoSuggestFromHistory(),
        style=PROMPT_STYLE,
        mouse_support=False,
    )

    while True:
        try:
            user_input = session.prompt(
                [("class:prompt", "\n  QueryMind > ")],
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print(Rule(style="bright_black"))
            console.print("  [bold cyan]Goodbye! 👋  QueryMind session ended.[/bold cyan]")
            console.print(Rule(style="bright_black"))
            console.print()
            database.disconnect()
            raise SystemExit(0)

        if not user_input:
            continue

        handled = _handle_command(user_input, cfg, conn)
        if not handled:
            _run_nl_query(user_input, cfg, conn, schema_text)


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Print version and exit."),
    setup: bool = typer.Option(False, "--setup", help="Re-run setup wizard."),
) -> None:
    """QueryMind 3 — Ask your database questions in plain English."""
    print_banner()

    if version:
        console.print(f"  QueryMind [bold magenta]{__version__}[/bold magenta]")
        raise typer.Exit(0)

    cfg = prompt_for_config()

    try:
        conn = database.connect(cfg)
    except Exception:
        console.print(
            "\n  [bold red]✗ Could not connect to the database.[/bold red]\n"
        )
        raise typer.Exit(1)

    _main_loop(cfg, conn)


def run():
    app()


if __name__ == "__main__":
    run()
