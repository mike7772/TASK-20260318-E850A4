import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ENV = os.getenv("ENV", "prod").lower()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET and ENV == "test":
    JWT_SECRET = "test-secret"
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set")
JWT_ALG = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(sub: str, role: str, permissions: list[str] | None = None, minutes: int = 120) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": sub, "role": role, "permissions": permissions or [], "exp": expire, "jti": secrets.token_hex(16), "typ": "access"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def create_refresh_token(sub: str, family_id: str, minutes: int = 60 * 24 * 7) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": sub, "exp": expire, "jti": secrets.token_hex(16), "fid": family_id, "typ": "refresh"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
