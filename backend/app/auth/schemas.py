
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=40,
        pattern=r"^[A-Za-z0-9_.-]+$"
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    full_name: str = Field(
        default="",
        max_length=120
    )
    role: Literal["member", "student", "faculty", "researcher"] = "member"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    full_name: str
    bio: str
    institution: str
    role: str
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageOut(BaseModel):
    message: str
