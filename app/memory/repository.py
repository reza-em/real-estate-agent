from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.db.repository import DEFAULT_DB_PATH
from app.models.memory import Interaction, UserProfile


class MemoryRepository:
    def __init__(self, path: Path = DEFAULT_DB_PATH) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        self._ensure_schema(connection)
        return connection

    def get_profile(self, user_id: str) -> UserProfile:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            feedback = connection.execute(
                """
                SELECT external_id, status
                FROM property_feedback
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchall()
            interaction_count = connection.execute(
                "SELECT COUNT(*) FROM interaction_history WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]

        profile = UserProfile(user_id=user_id, interaction_count=interaction_count)
        if row:
            profile.budget = row["budget"]
            profile.preferred_cities = json.loads(row["preferred_cities_json"] or "[]")
            profile.min_area = row["min_area"] or 0
            profile.preferences = row["preferences"] or ""
        profile.liked_properties = {
            item["external_id"] for item in feedback if item["status"] == "liked"
        }
        profile.rejected_properties = {
            item["external_id"] for item in feedback if item["status"] == "rejected"
        }
        return profile

    def save_profile(self, profile: UserProfile) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO user_profiles
                    (user_id, budget, preferred_cities_json, min_area, preferences)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    budget=excluded.budget,
                    preferred_cities_json=excluded.preferred_cities_json,
                    min_area=excluded.min_area,
                    preferences=excluded.preferences,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    profile.user_id,
                    profile.budget,
                    json.dumps(profile.preferred_cities, ensure_ascii=False),
                    profile.min_area,
                    profile.preferences,
                ),
            )

    def save_feedback(
        self, user_id: str, source: str, external_id: str, status: str
    ) -> None:
        if status not in {"liked", "rejected"}:
            raise ValueError("Feedback status must be liked or rejected")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO property_feedback (user_id, source, external_id, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, source, external_id) DO UPDATE SET
                    status=excluded.status,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, source, external_id, status),
            )

    def add_interaction(
        self, user_id: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO interaction_history (user_id, event_type, payload_json)
                VALUES (?, ?, ?)
                """,
                (user_id, event_type, json.dumps(payload, ensure_ascii=False)),
            )

    def recent_interactions(self, user_id: str, limit: int = 20) -> list[Interaction]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT event_type, payload_json, created_at
                FROM interaction_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, max(1, min(limit, 100))),
            ).fetchall()
        return [
            Interaction(
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                budget INTEGER,
                preferred_cities_json TEXT NOT NULL DEFAULT '[]',
                min_area INTEGER NOT NULL DEFAULT 0,
                preferences TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS property_feedback (
                user_id TEXT NOT NULL,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('liked', 'rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, source, external_id)
            );

            CREATE TABLE IF NOT EXISTS interaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_interactions_user_created
            ON interaction_history(user_id, created_at DESC);
            """
        )
