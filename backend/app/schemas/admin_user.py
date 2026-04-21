from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.auth import UserRead


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: Optional[str] = Field(default=None, max_length=128)
    status: str = Field(default="active", max_length=32)
    roles: list[str] = Field(default_factory=list)


class AdminUserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=64)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    email: Optional[str] = Field(default=None, max_length=128)
    status: Optional[str] = Field(default=None, max_length=32)
    roles: Optional[list[str]] = None


class AdminUserRead(UserRead):
    pass
