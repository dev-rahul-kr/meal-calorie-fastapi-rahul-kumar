import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Mapping, Any
from passlib.context import CryptContext
from app.core.config import get_settings

# one source of password hasher for the app
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Generate and return a bcrypt hash for the given password."""
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a raw password against its bcrypt hash."""
    return _pwd.verify(password, password_hash)


def create_access_token(
    subject: str,
    *,
    minutes: Optional[int] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> str:
    """Create a signed JWT for the subject"""
    s = get_settings()
    exp_minutes = minutes or s.JWT_EXPIRES_MIN

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)

    return jwt.encode(payload, s.JWT_SECRET.get_secret_value(), algorithm=s.JWT_ALGO)
