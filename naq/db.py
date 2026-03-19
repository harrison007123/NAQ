from rich.console import Console

console = Console()

_connection = None
_db_type: str = ""


def connect(cfg: dict):
    global _connection, _db_type

    db_cfg = cfg["database"]
    _db_type = db_cfg["type"].lower()

    try:
        if _db_type == "mysql":
            import mysql.connector
            conn = mysql.connector.connect(
                host=db_cfg["host"],
                port=int(db_cfg["port"]),
                user=db_cfg["user"],
                password=db_cfg["password"],
                database=db_cfg["name"],
                autocommit=False,
                connection_timeout=10,
            )
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchall()
            cur.close()

        elif _db_type == "postgresql":
            import psycopg2
            conn = psycopg2.connect(
                host=db_cfg["host"],
                port=int(db_cfg["port"]),
                user=db_cfg["user"],
                password=db_cfg["password"],
                dbname=db_cfg["name"],
                connect_timeout=10,
            )
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchall()
            cur.close()

        else:
            raise ValueError(f"Unsupported database type: {_db_type}")

        _connection = conn
        console.print(
            f"  [bold green]✓ Connected to "
            f"[cyan]{_db_type.upper()}[/cyan] "
            f"[cyan]{db_cfg['name']}[/cyan] "
            f"@ {db_cfg['host']}[/bold green]"
        )
        return conn

    except Exception as exc:
        console.print(f"[bold red]  ✗ Connection failed:[/bold red] {exc}")
        raise


def get_connection():
    if _connection is None:
        raise RuntimeError("Not connected to a database.")
    return _connection


def get_db_type() -> str:
    return _db_type


def disconnect() -> None:
    global _connection
    if _connection is not None:
        try:
            _connection.close()
        except Exception:
            pass
        _connection = None
