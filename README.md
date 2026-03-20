# NAQ

<div align="center">

```
███╗   ██╗ █████╗  ██████╗
████╗  ██║██╔══██╗██╔═══██╗
██╔██╗ ██║███████║██║   ██║
██║╚██╗██║██╔══██║██║▄▄ ██║
██║ ╚████║██║  ██║╚██████╔╝
╚═╝  ╚═══╝╚═╝  ╚═╝ ╚══▀▀═╝
```

**AI Natural Language → SQL Engine**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Groq-orange)](https://openai.com)
[![MySQL](https://img.shields.io/badge/DB-MySQL%20%7C%20PostgreSQL-4479a1?logo=mysql)](https://mysql.com)

</div>

---

## What is NAQ?

**NAQ** is an open-source terminal AI assistant that lets you query your SQL databases using **plain English**.

No SQL knowledge required. Just describe what you want, and NAQ generates and runs the query for you.

```
  NAQ > show me the top 10 customers by total revenue

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
| 🗄️ Multi-Database | **MySQL** |
| 🔍 Schema Awareness | Auto-loads your database schema for accurate SQL generation |
| 🛡️ Safety Layer | Blocks `DROP`, `TRUNCATE`, `ALTER`; confirms `DELETE`, `UPDATE` |
| 📊 Rich Tables | Beautiful terminal output with Rich |
| 🕐 History | Persistent query history with arrow-key recall |
| 🔧 Interactive REPL | Full interactive terminal with auto-suggestions |

---

## Installation


### Install from Source

```bash
git clone https://github.com/harrison007123/naq.git
cd naq
pip install -e .
```

---

## Quick Start

```bash
naq
```

On first run, the setup wizard will guide you through:

1. **LLM provider** — Choose OpenAI or Groq
2. **API key** — Your OpenAI or Groq key
3. **Database** — MySQL or PostgreSQL connection details


---

## Usage

### Natural Language Queries

```
NAQ > show top 10 customers by revenue
NAQ > how many orders were placed last month?
NAQ > list products with stock below 20
NAQ > which users signed up in the last 7 days?
NAQ > what is the average order value by country?
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
| `exit` / `quit` | Exit NAQ |

### CLI Flags

```bash
naq --version   # Print version
naq --setup     # Force re-run setup wizard
naq --help      # Show help
```

---

## Project Structure

```
naq/
├── naq/
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
├── pyproject.toml         # PEP 517 build config
├── requirements.txt       
├── LICENSE
├── README.md


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


Supported LLM models:
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Groq**: `llama3-70b-8192`, `llama3-8b-8192`, `mixtral-8x7b-32768`

---

## Safety

NAQ has a built-in SQL safety layer:

- `DROP`, `TRUNCATE`, `ALTER` → **permanently blocked**
- `DELETE`, `UPDATE`, `INSERT` → **requires explicit confirmation**
- `SELECT` → **always allowed**

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/harrison007123/naq).

```bash
git clone https://github.com/harrison007123/naq.git
cd naq
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## License

MIT © NAQ Contributors — see [LICENSE](LICENSE).
