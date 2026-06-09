from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="用户名，3-64 个字符")
    password: str = Field(min_length=6, max_length=128, description="登录密码，至少 6 位")
    email: Optional[str] = Field(default=None, description="邮箱地址")


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="用户名")
    password: str = Field(min_length=6, max_length=128, description="密码")


class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=64, description="新的用户名")
    email: Optional[str] = Field(default=None, max_length=128, description="新的邮箱地址")


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=6, max_length=128, description="当前密码")
    new_password: str = Field(min_length=6, max_length=128, description="新密码")


class PasswordReset(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="用户名")
    email: str = Field(min_length=5, max_length=128, description="绑定邮箱")
    new_password: str = Field(min_length=6, max_length=128, description="新密码")


class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    status: str
    created_at: datetime
    roles: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserRead] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
