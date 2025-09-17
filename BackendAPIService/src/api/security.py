from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import hmac
import base64
import json

from fastapi import HTTPException, status
from .config import get_settings

settings = get_settings()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(data: bytes, secret: str) -> str:
    # HMAC SHA-256 using hashlib via bcrypt's internal or stdlib hmac
    import hashlib
    signature = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).digest()
    return _b64url_encode(signature)


# PUBLIC_INTERFACE
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token for the given subject (typically user_id or email)."""
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    now = datetime.now(tz=timezone.utc)
    exp = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    to_sign = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = _sign(to_sign, settings.JWT_SECRET_KEY)
    return f"{header_b64}.{payload_b64}.{signature}"


# PUBLIC_INTERFACE
def decode_and_verify_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token signature and expiry. Returns payload dict if valid."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        header_b64, payload_b64, signature = parts
        expected_sig = _sign(f"{header_b64}.{payload_b64}".encode("utf-8"), settings.JWT_SECRET_KEY)
        # Constant time compare
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid signature")

        payload_raw = _b64url_decode(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))

        now = int(datetime.now(tz=timezone.utc).timestamp())
        if "exp" in payload and now >= int(payload["exp"]):
            raise ValueError("Token expired")

        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# PUBLIC_INTERFACE
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


# PUBLIC_INTERFACE
def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")
