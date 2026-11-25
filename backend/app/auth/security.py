
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from pwdlib import PasswordHash

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db, settings
from app.database.models import User, RevokedToken


password_hasher = PasswordHash.recommended()

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2.
    """
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its stored hash.
    """
    return password_hasher.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    """
    Create a signed JWT access token.
    """

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.access_token_minutes
    )

    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm
    )

    return token


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT.
    """

    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm]
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized

    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id = int(payload["sub"])
        token_id = payload["jti"]

    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise unauthorized

    revoked = db.scalar(
        select(RevokedToken).where(
            RevokedToken.jti == token_id
        )
    )

    if revoked:
        raise unauthorized

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise unauthorized

    return user
