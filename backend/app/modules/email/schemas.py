from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RegisterSendCode(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="注册用户名")
    email: str = Field(min_length=5, max_length=128, description="注册邮箱")


class RegisterConfirm(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="注册用户名")
    email: str = Field(min_length=5, max_length=128, description="注册邮箱")
    password: str = Field(min_length=6, max_length=128, description="注册密码")
    verification_code: str = Field(pattern=r"^\d{6}$", description="6 位验证码")


class ForgotPasswordSendCode(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="用户名")
    email: str = Field(min_length=5, max_length=128, description="绑定邮箱")


class ForgotPasswordConfirm(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="用户名")
    email: str = Field(min_length=5, max_length=128, description="绑定邮箱")
    new_password: str = Field(min_length=6, max_length=128, description="新密码")
    verification_code: str = Field(pattern=r"^\d{6}$", description="6 位验证码")


class EmailConfigWriteBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    smtp_host: str = Field(min_length=1, max_length=255)
    smtp_port: int = Field(ge=1, le=65535)
    smtp_username: Optional[str] = Field(default=None, max_length=255)
    smtp_password: Optional[str] = Field(default=None, max_length=255)
    sender_email: str = Field(min_length=5, max_length=128)
    sender_name: Optional[str] = Field(default=None, max_length=128)
    use_tls: bool = True
    use_ssl: bool = False
    enabled: bool = True


class EmailConfigCreate(EmailConfigWriteBase):
    pass


class EmailConfigUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    smtp_host: Optional[str] = Field(default=None, min_length=1, max_length=255)
    smtp_port: Optional[int] = Field(default=None, ge=1, le=65535)
    smtp_username: Optional[str] = Field(default=None, max_length=255)
    smtp_password: Optional[str] = Field(default=None, max_length=255)
    sender_email: Optional[str] = Field(default=None, min_length=5, max_length=128)
    sender_name: Optional[str] = Field(default=None, max_length=128)
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    enabled: Optional[bool] = None


class EmailConfigRead(BaseModel):
    name: str
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str] = None
    sender_email: str
    sender_name: Optional[str] = None
    use_tls: bool
    use_ssl: bool
    enabled: bool
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailConfigListResponse(BaseModel):
    items: list["EmailConfigRead"] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class EmailTemplateBase(BaseModel):
    template_key: str = Field(min_length=1, max_length=64)
    template_name: str = Field(min_length=1, max_length=128)
    subject: str = Field(min_length=1, max_length=255)
    body_text: str = Field(min_length=1)
    body_html: Optional[str] = None
    enabled: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    subject: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body_text: Optional[str] = Field(default=None, min_length=1)
    body_html: Optional[str] = None
    enabled: Optional[bool] = None


class EmailTemplateRead(EmailTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailTemplateListResponse(BaseModel):
    items: list["EmailTemplateRead"] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class VerificationCodeRead(BaseModel):
    email: str
    purpose: str
    expires_at: datetime
