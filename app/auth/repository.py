from __future__ import annotations

import sqlite3
from pathlib import Path

from app.db.repository import DEFAULT_DB_PATH
from app.models.auth import AuthUser


class AuthRepository:
    def __init__(self, path: Path = DEFAULT_DB_PATH) -> None:
        self.path = path

    def create_user(
        self, user_id: str, username: str, display_name: str, password_hash: str
    ) -> AuthUser:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO users (id, username, display_name, password_hash)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, username, display_name, password_hash),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("این نام کاربری قبلاً ثبت شده است") from exc
        return AuthUser(user_id, username, display_name)

    def credentials_for(self, username: str) -> tuple[AuthUser, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, display_name, password_hash
                FROM users WHERE username = ?
                """,
                (username,),
            ).fetchone()
        if row is None:
            return None
        return (
            AuthUser(row["id"], row["username"], row["display_name"]),
            row["password_hash"],
        )

    def find_by_id(self, user_id: str) -> AuthUser | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, username, display_name FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return AuthUser(**dict(row)) if row else None

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT
            )
            """
        )
        return connection

    def record_login(self, user_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,),
            )
