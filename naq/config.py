from typing import Optional
from rich.console import Console
from rich.prompt import Prompt

console = Console()

SUPPORTED_DB_TYPES = ["mysql", "postgresql"]
SUPPORTED_LLM_PROVIDERS = ["openai", "groq"]


def prompt_for_config() -> dict:
    console.print()
    from rich.panel import Panel
    console.print(
        Panel(
            "[bold yellow]⚙  Session Setup[/bold yellow]\n"
            "[dim]Credentials are used for this session only and are never saved.[/dim]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    console.print()

    console.print("[bold cyan]── LLM Configuration ──[/bold cyan]")
    llm_provider = ""
    while llm_provider not in SUPPORTED_LLM_PROVIDERS:
        llm_provider = Prompt.ask(
            "  LLM provider", choices=SUPPORTED_LLM_PROVIDERS, default="groq"
        ).lower()

    api_key = Prompt.ask(f"  {llm_provider.capitalize()} API key", password=True).strip()
    if not api_key:
        console.print("[red]  ✗ API key cannot be empty.[/red]")
        return prompt_for_config()

    if llm_provider == "groq":
        from naq.ai_engine import GROQ_MODELS
        console.print()
        console.print("  [bold]Select a Groq model:[/bold]")
        for i, m in enumerate(GROQ_MODELS, 1):
            console.print(f"  [cyan]{i}[/cyan]  {m['label']}")
        console.print()
        choice = ""
        while choice not in ("1", "2", "3"):
            choice = Prompt.ask("  Enter model number [1/2/3]", default="3").strip()
        model_name = GROQ_MODELS[int(choice) - 1]["model"]
        console.print(f"  [green]✓ Selected:[/green] [cyan]{model_name}[/cyan]")
    else:
        model_name = Prompt.ask("  Model name", default="gpt-4o-mini").strip()

    console.print()
    console.print("[bold cyan]── Database Configuration ──[/bold cyan]")
    db_type = ""
    while db_type not in SUPPORTED_DB_TYPES:
        db_type = Prompt.ask("  Database type", choices=SUPPORTED_DB_TYPES, default="mysql").lower()

    db_host     = Prompt.ask("  Host", default="localhost").strip()
    db_port_def = "3306" if db_type == "mysql" else "5432"
    db_port     = Prompt.ask("  Port", default=db_port_def).strip()
    db_user     = Prompt.ask("  Username").strip()
    db_password = Prompt.ask("  Password", password=True)
    db_name     = Prompt.ask("  Database name").strip()
    console.print()

    return {
        "llm": {
            "provider": llm_provider,
            "api_key":  api_key,
            "model":    model_name,
        },
        "database": {
            "type":     db_type,
            "host":     db_host,
            "port":     int(db_port),
            "user":     db_user,
            "password": db_password,
            "name":     db_name,
        },
    }


def config_exists() -> bool:
    return False

def load_config() -> dict:
    raise RuntimeError("Config is not persisted.")

def save_config(cfg: dict) -> None:
    pass

def run_setup_wizard() -> dict:
    return prompt_for_config()

def reconfigure() -> dict:
    return prompt_for_config()
