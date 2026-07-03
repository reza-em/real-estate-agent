from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

from app.models.analysis import Analysis
from app.models.listing import Listing


def _default_db_path() -> Path:
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parents[2] / "listings.db"

    data_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "RealEstateAgent"
    data_dir.mkdir(parents=True, exist_ok=True)
    database = data_dir / "listings.db"
    bundled_database = Path(getattr(sys, "_MEIPASS", ".")) / "listings.db"
    if not database.exists() and bundled_database.exists():
        shutil.copy2(bundled_database, database)
    return database


DEFAULT_DB_PATH = _default_db_path()


class ListingRepository:
    def __init__(self, path: Path = DEFAULT_DB_PATH) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        self._ensure_schema(connection)
        return connection

    def save(self, listings: list[Listing]) -> None:
        if not listings:
            return
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO listings
                    (source, external_id, title, price, area, location, url,
                     description, raw_json, latitude, longitude, address, city,
                     location_precision)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    title=excluded.title, price=excluded.price, area=excluded.area,
                    location=excluded.location, url=excluded.url,
                    description=excluded.description, raw_json=excluded.raw_json,
                    latitude=excluded.latitude, longitude=excluded.longitude,
                    address=excluded.address, city=excluded.city,
                    location_precision=excluded.location_precision,
                    seen_at=CURRENT_TIMESTAMP
                """,
                [
                    (
                        item.source,
                        item.external_id,
                        item.title,
                        item.price,
                        item.area,
                        item.location,
                        item.url,
                        item.description,
                        json.dumps(item.raw, ensure_ascii=False),
                        item.latitude,
                        item.longitude,
                        item.address,
                        item.city,
                        item.location_precision,
                    )
                    for item in listings
                ],
            )

    def get_cached_geocode(
        self, query: str
    ) -> tuple[float, float, str | None, str] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT latitude, longitude, address, precision
                FROM geocode_cache
                WHERE query = ?
                """,
                (query,),
            ).fetchone()
        if row is None:
            return None
        return row["latitude"], row["longitude"], row["address"], row["precision"]

    def save_geocode(
        self,
        query: str,
        latitude: float,
        longitude: float,
        address: str | None,
        precision: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO geocode_cache
                    (query, latitude, longitude, address, precision)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(query) DO UPDATE SET
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    address=excluded.address,
                    precision=excluded.precision,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (query, latitude, longitude, address, precision),
            )

    def save_analyses(self, analyses: list[Analysis]) -> None:
        if not analyses:
            return
        with self.connect() as connection:
            connection.executemany(
                """
                UPDATE listings
                SET score = ?, analysis = ?
                WHERE external_id = ?
                """,
                [
                    (
                        item.score,
                        json.dumps(
                            {"summary": item.summary, "risks": item.risks},
                            ensure_ascii=False,
                        ),
                        item.external_id,
                    )
                    for item in analyses
                ],
            )

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                price INTEGER,
                area INTEGER,
                latitude REAL,
                longitude REAL,
                address TEXT,
                city TEXT,
                location_precision TEXT NOT NULL DEFAULT 'unknown',
                location TEXT,
                url TEXT NOT NULL,
                description TEXT,
                score REAL,
                analysis TEXT,
                raw_json TEXT,
                seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source, external_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS geocode_cache (
                query TEXT PRIMARY KEY,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                precision TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(listings)")
        }
        migrations = {
            "area": "INTEGER",
            "latitude": "REAL",
            "longitude": "REAL",
            "address": "TEXT",
            "city": "TEXT",
            "location_precision": "TEXT NOT NULL DEFAULT 'unknown'",
        }
        for column, definition in migrations.items():
            if column not in columns:
                connection.execute(
                    f"ALTER TABLE listings ADD COLUMN {column} {definition}"
                )
