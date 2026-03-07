# QueryMind 3

<div align="center">

```
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗███╗   ███╗██╗███╗   ██╗██████╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝████╗ ████║██║████╗  ██║██╔══██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝ ██╔████╔██║██║██╔██╗ ██║██║  ██║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝  ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║   ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝
```

**AI Natural Language → SQL Engine**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Groq-orange)](https://openai.com)
[![MySQL](https://img.shields.io/badge/DB-MySQL%20%7C%20PostgreSQL-4479a1?logo=mysql)](https://mysql.com)

</div>

---

## What is QueryMind 3?

**QueryMind 3** is an open-source terminal AI assistant that lets you query your SQL databases using **plain English**.

No SQL knowledge required. Just describe what you want, and QueryMind generates and runs the query for you.

```
  QueryMind > show me the top 10 customers by total revenue

  ┌──────────────┬──────────────┐
  │ customer     │ revenue      │
  ├──────────────┼──────────────┤
  │ Alice Corp   │ 128,400.00   │
  │ Beta Systems │  98,200.00   │
  │ …            │ …            │
  └──────────────┴──────────────┘
  10 rows returned.
```

---

## Features

| Feature | Description |
|---|---|
| 🗣️ Natural Language | Ask questions in plain English |
| 🤖 Multi-LLM | Supports **OpenAI** (GPT-4o, GPT-4o-mini) and **Groq** (Llama 3, Mixtral) |
| 🗄️ Multi-Database | **MySQL** and **PostgreSQL** |
| 🔍 Schema Awareness | Auto-loads your database schema for accurate SQL generation |
| 🛡️ Safety Layer | Blocks `DROP`, `TRUNCATE`, `ALTER`; confirms `DELETE`, `UPDATE` |
| 📊 Rich Tables | Beautiful terminal output with Rich |
| 🕐 History | Persistent query history with arrow-key recall |
| 🔧 Interactive REPL | Full interactive terminal with auto-suggestions |

---

## Installation

### Run with Docker (Recommended)

You can run QueryMind in an isolated container without installing Python dependencies on your host.

```bash
docker run -it --rm --network host bennett007030/querymind3
```
*Note for macOS/Windows users*: If your database is running on `localhost` outside of Docker, use `host.docker.internal` instead of `localhost` when prompted for the database host.

### One-Line Installer (Windows)

```powershell
irm https://raw.githubusercontent.com/harrison007123/querymind3/main/install.ps1 | iex
```

### One-Line Installer (Linux / macOS / WSL)

```bash
curl -sSL https://raw.githubusercontent.com/harrison007123/querymind3/main/install.sh | bash
```

### pip (All Platforms)

```bash
pip install querymind3
```

### Install from Source

```bash
git clone https://github.com/harrison007123/querymind3.git
cd querymind3
pip install -e .
```

---

## Quick Start

```bash
querymind
```

On first run, the setup wizard will guide you through:

1. **LLM provider** — Choose OpenAI or Groq
2. **API key** — Your OpenAI or Groq key
3. **Database** — MySQL or PostgreSQL connection details

Configuration is saved to `~/.querymind/config.json`.

---

## Usage

### Natural Language Queries

```
QueryMind > show top 10 customers by revenue
QueryMind > how many orders were placed last month?
QueryMind > list products with stock below 20
QueryMind > which users signed up in the last 7 days?
QueryMind > what is the average order value by country?
```

### Built-in Commands

| Command | Description |
|---|---|
| `help` | Show all available commands |
| `schema` | Display full database schema |
| `schema refresh` | Force reload schema from database |
| `history` | View recent query history |
| `history clear` | Clear query history |
| `config` | Re-run the setup wizard |
| `exit` / `quit` | Exit QueryMind |

### CLI Flags

```bash
querymind --version   # Print version
querymind --setup     # Force re-run setup wizard
querymind --help      # Show help
```

---

## Project Structure

```
querymind3/
├── querymind/
│   ├── __init__.py        # Package metadata & version
│   ├── cli.py             # Interactive REPL & Typer entry point
│   ├── banner.py          # ASCII banner & startup display
│   ├── config.py          # Setup wizard & config management
│   ├── db.py              # SQLAlchemy connection manager
│   ├── schema_loader.py   # Auto-detect tables, columns, FKs
│   ├── safety.py          # SQL safety layer
│   ├── ai_engine.py       # LLM integration (OpenAI / Groq)
│   ├── executor.py        # SQL execution → pandas DataFrame
│   └── utils.py           # History, Rich table renderer
├── install.sh             # One-line bash installer
├── pyproject.toml         # PEP 517 build config
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Technology Stack

| Library | Purpose |
|---|---|
| [`typer`](https://typer.tiangolo.com/) | CLI framework |
| [`rich`](https://rich.readthedocs.io/) | Terminal UI & tables |
| [`sqlalchemy`](https://www.sqlalchemy.org/) | Database connectivity |
| [`pandas`](https://pandas.pydata.org/) | Result formatting |
| [`prompt_toolkit`](https://python-prompt-toolkit.readthedocs.io/) | Interactive REPL |
| [`requests`](https://requests.readthedocs.io/) | LLM API calls |

---

## Configuration

Config lives at `~/.querymind/config.json`:

```json
{
  "llm": {
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-4o-mini"
  },
  "database": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "...",
    "name": "mydb"
  }
}
```

Supported LLM models:
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Groq**: `llama3-70b-8192`, `llama3-8b-8192`, `mixtral-8x7b-32768`

---

## Safety

QueryMind 3 has a built-in SQL safety layer:

- `DROP`, `TRUNCATE`, `ALTER` → **permanently blocked**
- `DELETE`, `UPDATE`, `INSERT` → **requires explicit confirmation**
- `SELECT` → **always allowed**

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/querymind/querymind3).

```bash
git clone https://github.com/harrison007123/querymind3.git
cd querymind3
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## License

MIT © QueryMind Contributors — see [LICENSE](LICENSE).
