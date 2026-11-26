
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import User, RevokedToken
from .security import hash_password, verify_password, decode_access_token


def register(db: Session, data):

    username = data.username.strip().lower()
    email = str(data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(
            or_(
                func.lower(User.email) == email,
                func.lower(User.username) == username
            )
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email or username is already registered"
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        role=data.role,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email or username is already registered"
        )

    return user


def authenticate(db: Session, email: str, password: str):

    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(
            func.lower(User.email) == normalized_email
        )
    )

    if (
        not user
        or not verify_password(password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


def revoke_token(db: Session, token: str):

    payload = decode_access_token(token)

    token_id = payload["jti"]

    expires_at = payload["exp"]

    expiration = datetime.fromtimestamp(
        expires_at,
        tz=timezone.utc
    )

    revoked_token = RevokedToken(
        jti=token_id,
        expires_at=expiration
    )

    db.merge(revoked_token)
    db.commit()

    return True
