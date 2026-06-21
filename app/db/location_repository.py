from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.db.repository import DEFAULT_DB_PATH


class LocationCatalogRepository:
    def __init__(self, path: Path = DEFAULT_DB_PATH) -> None:
        self.path = path

    def load(self) -> tuple[dict[str, object], datetime] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json, fetched_at FROM location_catalog_cache WHERE id = 1"
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload_json"]), datetime.fromisoformat(row["fetched_at"])

    def save(self, payload: dict[str, object]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO location_catalog_cache (id, payload_json, fetched_at)
                VALUES (1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    fetched_at=CURRENT_TIMESTAMP
                """,
                (json.dumps(payload, ensure_ascii=False),),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS location_catalog_cache (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                payload_json TEXT NOT NULL,
                fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return connection
