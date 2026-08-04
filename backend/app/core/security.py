"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings


settings = get_settings()

# bcrypt is a strong one-way hashing algorithm for storing passwords safely.
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a plain-text password before storing it in the database."""

    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check whether a login password matches the stored password hash."""

    return password_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Create a signed JWT token for a user.

    The `subject` is usually the user's database ID. The token also includes an
    expiration time so old tokens stop working automatically.
    """

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Return the user ID from a JWT token, or None if the token is invalid."""

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
    except JWTError:
        return None

    if subject is None:
        return None

    return str(subject)
