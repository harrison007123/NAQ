import pandas as pd
from rich.console import Console
from naq.db import get_db_type

console = Console()


class QueryResult:
    def __init__(self, sql: str, df: pd.DataFrame, row_count: int):
        self.sql = sql
        self.df = df
        self.row_count = row_count
        self.is_empty = df.empty

    def __repr__(self) -> str:
        return f"<QueryResult rows={self.row_count} columns={list(self.df.columns)}>"


def _split_statements(sql: str) -> list:
    statements = []
    current = []
    in_single = False

    for ch in sql:
        if ch == "'":
            in_single = not in_single
        elif ch == ";" and not in_single:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            continue
        current.append(ch)

    remainder = "".join(current).strip()
    if remainder:
        statements.append(remainder)
    return statements


def _execute_mysql(conn, statements: list) -> QueryResult:
    last_df = pd.DataFrame()
    total_affected = 0
    had_rows = False
    original_sql = "; ".join(statements)

    cursor = conn.cursor(dictionary=True)
    try:
        for query in statements:
            cursor.execute(query)
            if cursor.with_rows:
                rows = cursor.fetchall()
                if rows:
                    last_df = pd.DataFrame(rows)
                    had_rows = True
            else:
                total_affected += cursor.rowcount or 0
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"Query execution failed: {exc}") from exc
    finally:
        cursor.close()

    if had_rows:
        return QueryResult(sql=original_sql, df=last_df, row_count=len(last_df))
    summary = pd.DataFrame({"status": [f"{total_affected} row(s) affected across {len(statements)} statement(s)"]})
    return QueryResult(sql=original_sql, df=summary, row_count=total_affected)


def _execute_postgresql(conn, statements: list) -> QueryResult:
    last_df = pd.DataFrame()
    total_affected = 0
    had_rows = False
    original_sql = "; ".join(statements)

    cursor = conn.cursor()
    try:
        for query in statements:
            cursor.execute(query)
            if cursor.description:
                cols = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                last_df = pd.DataFrame(rows, columns=cols)
                had_rows = True
            else:
                total_affected += cursor.rowcount or 0
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"Query execution failed: {exc}") from exc
    finally:
        cursor.close()

    if had_rows:
        return QueryResult(sql=original_sql, df=last_df, row_count=len(last_df))
    summary = pd.DataFrame({"status": [f"{total_affected} row(s) affected across {len(statements)} statement(s)"]})
    return QueryResult(sql=original_sql, df=summary, row_count=total_affected)


def execute_query(conn, sql: str) -> QueryResult:
    statements = _split_statements(sql)
    if not statements:
        raise RuntimeError("No executable SQL statements found in the LLM response.")

    db_type = get_db_type()
    if db_type == "mysql":
        return _execute_mysql(conn, statements)
    elif db_type == "postgresql":
        return _execute_postgresql(conn, statements)
    else:
        raise RuntimeError(f"Unsupported database type: {db_type}")
