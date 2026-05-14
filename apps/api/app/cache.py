"""SQLite-backed TTL cache.

One file on disk, namespace + key + payload + fetched_at timestamp.
Each method opens its own connection; SQLite handles its own locking.
Inspect with: ``sqlite3 data/cache.sqlite "select namespace, key, fetched_at from cache;"``
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    namespace TEXT NOT NULL,
    key TEXT NOT NULL,
    payload TEXT NOT NULL,
    fetched_at INTEGER NOT NULL,
    PRIMARY KEY (namespace, key)
)
"""


class TTLCache:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def get(self, namespace: str, key: str, ttl_seconds: int) -> Optional[Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload, fetched_at FROM cache WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        if row is None:
            return None
        payload, fetched_at = row
        if time.time() - fetched_at > ttl_seconds:
            return None
        return json.loads(payload)

    def set(self, namespace: str, key: str, payload: Any) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cache (namespace, key, payload, fetched_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    payload = excluded.payload,
                    fetched_at = excluded.fetched_at
                """,
                (namespace, key, json.dumps(payload), int(time.time())),
            )

    def purge_namespace(self, namespace: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE namespace = ?",
                (namespace,),
            )
            return cursor.rowcount
