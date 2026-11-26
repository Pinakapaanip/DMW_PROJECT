
import ipaddress
import secrets

from fastapi import APIRouter, Depends, status
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.connection import settings
from app.database.models import User

from app.auth.schemas import (
    RegisterIn,
    LoginIn,
    UserOut,
    TokenOut,
    MessageOut
)

from app.auth.service import (
    register,
    authenticate,
    revoke_token
)

from app.auth.security import (
    create_access_token,
    get_current_user,
    hash_password,
    bearer_scheme
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["F1 Authentication"]
)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED
)
def register_route(
    data: RegisterIn,
    db: Session = Depends(get_db)
):
    user = register(db, data)

    return user


@router.post(
    "/login",
    response_model=TokenOut
)
def login_route(
    data: LoginIn,
    db: Session = Depends(get_db)
):

    user = authenticate(
        db,
        str(data.email),
        data.password
    )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post(
    "/dev-login",
    response_model=TokenOut
)
def dev_login_route(
    request: Request,
    db: Session = Depends(get_db)
):
    if not settings.allow_dev_login:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    client = request.client
    try:
        is_local_client = client is not None and ipaddress.ip_address(client.host).is_loopback
    except ValueError:
        is_local_client = False

    if not is_local_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is only available from this computer"
        )

    user = db.scalar(
        select(User).where(User.email == "local-demo@example.com")
    )
    if user is None:
        user = User(
            username="local-demo",
            email="local-demo@example.com",
            password_hash=hash_password(secrets.token_urlsafe(32)),
            full_name="Local Demo User",
            role="member",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The local demo account is inactive"
        )

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": user
    }


@router.get(
    "/me",
    response_model=UserOut
)
def get_my_profile(
    user: User = Depends(get_current_user)
):
    return user


@router.post(
    "/logout",
    response_model=MessageOut
)
def logout_route(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    revoke_token(
        db,
        credentials.credentials
    )

    return {
        "message": "Successfully logged out"
    }
