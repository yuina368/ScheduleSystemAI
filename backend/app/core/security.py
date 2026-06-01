from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


def _password_bytes(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_password_bytes(plain_password), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject = payload.get("sub")
        return int(subject) if subject is not None else None
    except (JWTError, ValueError):
        return None
