import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box

console = Console()

BANNER = r"""
███╗   ██╗ █████╗  ██████╗
████╗  ██║██╔══██╗██╔═══██╗
██╔██╗ ██║███████║██║   ██║
██║╚██╗██║██╔══██║██║▄▄ ██║
██║ ╚████║██║  ██║╚██████╔╝
╚═╝  ╚═══╝╚═╝  ╚═╝ ╚══▀▀═╝
"""


def print_banner() -> None:
    console.print()
    banner=Text(BANNER, style="bold cyan")
    console.print(Align.center(banner))
    title_line = Text()
    title_line.append("  NAQ ", style="bold white")
    title_line.append("3", style="bold magenta")
    title_line.append("  ·  ", style="dim white")
    title_line.append("AI Natural Language ", style="bold green")
    title_line.append("→ ", style="bold yellow")
    title_line.append("SQL Engine", style="bold green")
    console.print(Align.center(title_line))
    console.print()

    info_left  = Text("  ⚡ OpenAI  ·  Groq LLM", style="dim cyan")
    info_mid   = Text("  🗄  MySQL  ·  PostgreSQL", style="dim cyan")
    info_right = Text("  🛡  Safety Layer  ·  Schema Aware", style="dim cyan")
    console.print(Columns([info_left, info_mid, info_right], equal=True, expand=True))
    console.print()

    console.print(
        Panel(
            Align.center(
                "[dim]Type [bold cyan]help[/bold cyan] for commands  "
                "·  [bold cyan]schema[/bold cyan] to view tables  "
                "·  [bold cyan]exit[/bold cyan] to quit[/dim]\n"
                "[dim]─────────────────────────────────────────────────[/dim]\n"
                "[dim]Developed by [/dim][bold magenta]Harrison Bennett J[/bold magenta][dim]  ·  v3.0.0[/dim]"
            ),
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )
    console.print()


def animated_startup(steps: list) -> None:
    console.print()
    with Progress(
        SpinnerColumn(style="bold cyan"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30, style="cyan", complete_style="bold green"),
        TextColumn("[bold green]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progress:
        for label in steps:
            task = progress.add_task(label, total=100)
            for _ in range(20):
                time.sleep(0.02)
                progress.advance(task, 5)
    console.print()


def thinking_steps(steps: list) -> None:
    for step in steps:
        console.print(f"  [bold cyan]›[/bold cyan] [dim]{step}[/dim]")
        time.sleep(0.3)
    console.print()
