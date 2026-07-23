from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator

try:
    import psycopg2
    from psycopg2 import pool as pg_pool
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore
    pg_pool = None  # type: ignore

_pools: dict[str, object] = {}
_lock = Lock()


def get_pool(dsn: str, *, minconn: int = 1, maxconn: int = 10):
    if psycopg2 is None or pg_pool is None:
        raise RuntimeError("psycopg2 is required for connection pooling")
    with _lock:
        existing = _pools.get(dsn)
        if existing is not None:
            return existing
        created = pg_pool.ThreadedConnectionPool(minconn, maxconn, dsn)
        _pools[dsn] = created
        return created


@contextmanager
def pooled_connection(dsn: str) -> Iterator:
    """Borrow a pooled Postgres connection (commit on success, rollback on error)."""
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is required")
    pool = get_pool(dsn)
    conn = pool.getconn()
    try:
        yield conn
        if not conn.closed:
            conn.commit()
    except Exception:
        if not conn.closed:
            conn.rollback()
        raise
    finally:
        pool.putconn(conn)
