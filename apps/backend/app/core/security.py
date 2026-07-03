from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.domain.exceptions import InvalidTokenError

settings = get_settings()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    # passlib is untyped, so mypy sees Any here — the cast documents the real contract.
    return str(_pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bool(_pwd_context.verify(plain_password, hashed_password))


def _create_token(subject: UUID, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(subject), "exp": now + expires_delta, "type": token_type}
    return str(jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM))


def create_access_token(user_id: UUID) -> str:
    return _create_token(user_id, timedelta(minutes=settings.access_token_expire_minutes), "access")


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(user_id, timedelta(days=settings.refresh_token_expire_days), "refresh")


def decode_token(token: str, expected_type: str) -> UUID:
    """Decode and validate a JWT, raising InvalidTokenError on any failure.
    Callers never see jose's exceptions — only this domain-level error.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token")

    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Token is missing its subject")

    return UUID(subject)
