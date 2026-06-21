from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import unicodedata
import uuid

from app.auth.repository import AuthRepository
from app.models.auth import AuthUser


class AuthService:
    SCRYPT_N = 2**14
    SCRYPT_R = 8
    SCRYPT_P = 1

    def __init__(self, repository: AuthRepository | None = None) -> None:
        self.repository = repository or AuthRepository()

    def register(
        self,
        username: str,
        password: str,
        password_confirmation: str,
        display_name: str = "",
    ) -> AuthUser:
        normalized = self.normalize_username(username)
        self._validate_username(normalized)
        self._validate_password(password)
        if password != password_confirmation:
            raise ValueError("تکرار رمز عبور مطابقت ندارد")
        name = display_name.strip()[:80] or normalized
        return self.repository.create_user(
            uuid.uuid4().hex,
            normalized,
            name,
            self._hash_password(password),
        )

    def authenticate(self, username: str, password: str) -> AuthUser:
        normalized = self.normalize_username(username)
        credentials = self.repository.credentials_for(normalized)
        if credentials is None or not self._verify_password(
            password, credentials[1]
        ):
            raise ValueError("نام کاربری یا رمز عبور اشتباه است")
        self.repository.record_login(credentials[0].id)
        return credentials[0]

    @staticmethod
    def normalize_username(username: str) -> str:
        return unicodedata.normalize("NFKC", username).strip().casefold()

    @staticmethod
    def _validate_username(username: str) -> None:
        if not 3 <= len(username) <= 40:
            raise ValueError("نام کاربری باید بین ۳ تا ۴۰ کاراکتر باشد")
        if not re.fullmatch(r"[\w.\-]+", username, flags=re.UNICODE):
            raise ValueError("نام کاربری فقط می‌تواند شامل حروف، عدد، نقطه و خط تیره باشد")

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise ValueError("رمز عبور باید حداقل ۸ کاراکتر باشد")
        if not any(character.isdigit() for character in password):
            raise ValueError("رمز عبور باید حداقل یک عدد داشته باشد")
        if not any(character.isalpha() for character in password):
            raise ValueError("رمز عبور باید حداقل یک حرف داشته باشد")

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=self.SCRYPT_N,
            r=self.SCRYPT_R,
            p=self.SCRYPT_P,
            dklen=32,
        )
        return "$".join(
            (
                "scrypt",
                str(self.SCRYPT_N),
                str(self.SCRYPT_R),
                str(self.SCRYPT_P),
                base64.b64encode(salt).decode("ascii"),
                base64.b64encode(digest).decode("ascii"),
            )
        )

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, n, r, p, salt_text, digest_text = encoded.split("$")
            if algorithm != "scrypt":
                return False
            digest = hashlib.scrypt(
                password.encode("utf-8"),
                salt=base64.b64decode(salt_text),
                n=int(n),
                r=int(r),
                p=int(p),
                dklen=32,
            )
            return hmac.compare_digest(digest, base64.b64decode(digest_text))
        except (ValueError, TypeError):
            return False
