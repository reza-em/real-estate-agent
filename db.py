from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scraper import Listing


DB_PATH = Path(__file__).with_name("listings.db")


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            title TEXT NOT NULL,
            price INTEGER,
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
    return connection


def save_listings(listings: list[Listing], path: Path = DB_PATH) -> None:
    with connect(path) as connection:
        connection.executemany(
            """
            INSERT INTO listings
                (source, external_id, title, price, location, url, description, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                title=excluded.title, price=excluded.price,
                location=excluded.location, url=excluded.url,
                description=excluded.description, raw_json=excluded.raw_json,
                seen_at=CURRENT_TIMESTAMP
            """,
            [
                (
                    item.source,
                    item.external_id,
                    item.title,
                    item.price,
                    item.location,
                    item.url,
                    item.description,
                    json.dumps(item.raw, ensure_ascii=False),
                )
                for item in listings
            ],
        )
