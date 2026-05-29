from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: int, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": str(subject), "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def build_payment_signature(
    account_id: int,
    amount: Any,
    transaction_id: str,
    user_id: int,
) -> str:
    raw = f"{account_id}{amount}{transaction_id}{user_id}{settings.payment_secret_key}"
    return hashlib.sha256(raw.encode()).hexdigest()
