"""
schema_loader.py — Inspect the database schema using native connectors.

MySQL:      queries INFORMATION_SCHEMA via mysql-connector-python
PostgreSQL: queries information_schema via psycopg2

No SQLAlchemy dependency.
"""

from typing import Dict, List
from rich.console import Console
from sqlalchemy import schema
from naq.db import get_db_type

console = Console()

# Cache:  { db_name: { "raw": {...}, "text": "..." } }
_schema_cache: Dict[str, dict] = {}


# ── MySQL Schema ──────────────────────────────────────────────────────────────
def _fetch_schema_mysql(conn, db_name: str) -> dict:
    cur = conn.cursor(dictionary=True)
    schema: Dict[str, dict] = {}

    # Get all tables
    cur.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' "
        "ORDER BY TABLE_NAME",
        (db_name,),
    )
    tables = [r["TABLE_NAME"] for r in cur.fetchall()]

    for table in tables:
        # Columns
        cur.execute(
            "SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY, IS_NULLABLE "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
            "ORDER BY ORDINAL_POSITION",
            (db_name, table),
        )
        columns = []
        for col in cur.fetchall():
            columns.append({
                "name":     col["COLUMN_NAME"],
                "type":     col["COLUMN_TYPE"],
                "pk":       col["COLUMN_KEY"] == "PRI",
                "nullable": col["IS_NULLABLE"] == "YES",
            })

        # Foreign keys
        cur.execute(
            "SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
            "FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
            "AND REFERENCED_TABLE_NAME IS NOT NULL",
            (db_name, table),
        )
        fks = [
            {
                "column":    r["COLUMN_NAME"],
                "ref_table": r["REFERENCED_TABLE_NAME"],
                "ref_col":   r["REFERENCED_COLUMN_NAME"],
            }
            for r in cur.fetchall()
        ]
        schema[table] = {"columns": columns, "foreign_keys": fks}

    cur.close()

    return schema


# ── PostgreSQL Schema ─────────────────────────────────────────────────────────
def load_all_tables(conn,db_name):
    pass
def _fetch_schema_postgresql(conn, db_name: str) -> dict:
    cur = conn.cursor()
    schema: Dict[str, dict] = {}

    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
        "ORDER BY table_name"
    )
    tables = [r[0] for r in cur.fetchall()]

    for table in tables:
        cur.execute(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s "
            "ORDER BY ordinal_position",
            (table,),
        )
        raw_cols = cur.fetchall()

        # Primary keys
        cur.execute(
            "SELECT kcu.column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "  AND tc.table_schema = kcu.table_schema "
            "WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = %s",
            (table,),
        )
        pk_cols = {r[0] for r in cur.fetchall()}

        columns = [
            {
                "name":     col[0],
                "type":     col[1],
                "pk":       col[0] in pk_cols,
                "nullable": col[2] == "YES",
            }
            for col in raw_cols
        ]

        # Foreign keys
        cur.execute(
            "SELECT kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_col "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "JOIN information_schema.constraint_column_usage ccu "
            "  ON ccu.constraint_name = tc.constraint_name "
            "WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s",
            (table,),
        )
        fks = [
            {"column": r[0], "ref_table": r[1], "ref_col": r[2]}
            for r in cur.fetchall()
        ]
        schema[table] = {"columns": columns, "foreign_keys": fks}

    cur.close()
    return schema


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_schema(conn, cfg: dict, force_refresh: bool = False) -> dict:
    """
    Inspect the connected database and return a schema dict.
    Results are cached per database name.
    """
    db_name = cfg["database"]["name"]
    db_type = get_db_type()

    if not force_refresh and db_name in _schema_cache:
        return _schema_cache[db_name]["raw"]

    if db_type == "mysql":
        raw = _fetch_schema_mysql(conn, db_name)
    elif db_type == "postgresql":
        raw = _fetch_schema_postgresql(conn, db_name)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    _schema_cache[db_name] = {
        "raw":  raw,
        "text": _schema_to_text(raw),
    }
    return raw


def _schema_to_text(schema: dict) -> str:
    
    lines: List[str] = []
    for table, info in schema.items():
        col_parts = []
        for col in info["columns"]:
            pk_marker = " [PK]" if col["pk"] else ""
            col_parts.append(f"{col['name']} {col['type']}{pk_marker}")
        lines.append(f"Table: {table}")
        lines.append(f"  Columns: {', '.join(col_parts)}")
        if info["foreign_keys"]:
            fk_parts = [
                f"{fk['column']} → {fk['ref_table']}.{fk['ref_col']}"
                for fk in info["foreign_keys"]
            ]
            lines.append(f"  Foreign Keys: {', '.join(fk_parts)}")
    return "\n".join(lines)
def log(message):
    with open("output.log", "a") as f:
        f.write(message + "\n")

def schema_to_text(schema):
    """Return a compact LLM-friendly text representation of the schema."""
    x=_schema_to_text(schema)
    log(x)
    return x 




def clear_cache() -> None:
    """Invalidate the schema cache."""
    _schema_cache.clear()
