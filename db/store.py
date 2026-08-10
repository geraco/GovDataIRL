"""Thin sqlite3 wrapper — no ORM, matches the rest of the stack's local-first pattern."""
import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA_PATH = DB_PATH.parent / "schema.sql"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text())
        _migrate(conn)


def _migrate(conn):
    """Additive column migrations for DBs created before a schema change."""
    existing = {r[1] for r in conn.execute("PRAGMA table_info(reports)")}
    if "interestingness_score" not in existing:
        conn.execute("ALTER TABLE reports ADD COLUMN interestingness_score INTEGER")
    if "dataset_last_updated" not in existing:
        conn.execute("ALTER TABLE reports ADD COLUMN dataset_last_updated TEXT")


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert(conn, table, row: dict):
    cols = ", ".join(row.keys())
    placeholders = ", ".join(f":{k}" for k in row)
    updates = ", ".join(f"{k}=excluded.{k}" for k in row if k not in ("resource_id", "run_id", "report_id"))
    pk = {"candidates": "resource_id", "runs": "run_id", "reports": "report_id"}[table]
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) ON CONFLICT({pk}) DO UPDATE SET {updates}"
    conn.execute(sql, row)
