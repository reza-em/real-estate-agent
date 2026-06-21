import sqlite3
from pathlib import Path

import pytest

from app.auth.repository import AuthRepository
from app.auth.service import AuthService


def test_registration_hashes_password_and_login_restores_same_user(tmp_path: Path):
    path = tmp_path / "auth.db"
    auth = AuthService(AuthRepository(path))
    registered = auth.register("Test.User", "secure123", "secure123", "کاربر تست")

    with sqlite3.connect(path) as connection:
        stored_hash = connection.execute(
            "SELECT password_hash FROM users WHERE id = ?", (registered.id,)
        ).fetchone()[0]
    assert "secure123" not in stored_hash
    assert stored_hash.startswith("scrypt$")

    logged_in = auth.authenticate("test.user", "secure123")
    assert logged_in == registered


def test_auth_rejects_duplicate_username_and_wrong_password(tmp_path: Path):
    auth = AuthService(AuthRepository(tmp_path / "auth.db"))
    auth.register("my-user", "password1", "password1")
    with pytest.raises(ValueError, match="قبلاً ثبت شده"):
        auth.register("MY-USER", "password1", "password1")
    with pytest.raises(ValueError, match="اشتباه"):
        auth.authenticate("my-user", "wrong-pass1")


def test_auth_validates_password_strength(tmp_path: Path):
    auth = AuthService(AuthRepository(tmp_path / "auth.db"))
    with pytest.raises(ValueError, match="حداقل ۸"):
        auth.register("user", "a1", "a1")
