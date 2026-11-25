
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
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
