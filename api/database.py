import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "../data/policies.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()
