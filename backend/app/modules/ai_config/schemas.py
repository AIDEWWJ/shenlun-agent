from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AiConfigBase(BaseModel):
    provider: str = Field(min_length=1, max_length=64, description="模型提供方，例如 openai、qwen、deepseek")
    model_name: str = Field(min_length=1, max_length=128, description="模型名称")
    api_key: str = Field(min_length=1, max_length=255, description="模型服务 API Key")
    base_url: Optional[str] = Field(default=None, max_length=255, description="模型服务接口地址，可为空")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="生成温度，通常 0-2")
    is_default: bool = Field(default=False, description="是否设为默认配置")


class AiConfigCreate(AiConfigBase):
    scope: Literal["user"] = "user"


class AiConfigUpdate(BaseModel):
    provider: Optional[str] = Field(default=None, min_length=1, max_length=64)
    model_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    api_key: Optional[str] = Field(default=None, min_length=1, max_length=255)
    base_url: Optional[str] = Field(default=None, max_length=255)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    is_default: Optional[bool] = None


class AiConfigRead(BaseModel):
    id: int
    user_id: Optional[int] = None
    scope: str
    created_by: Optional[int] = None
    provider: str
    model_name: str
    base_url: Optional[str] = None
    temperature: float
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AiConfigListResponse(BaseModel):
    items: list["AiConfigRead"] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class AiConfigAdminCreate(AiConfigBase):
    scope: Literal["system"] = "system"
    user_id: Optional[int] = None


class AiConfigAdminUpdate(AiConfigUpdate):
    scope: Optional[Literal["system", "user"]] = None
    user_id: Optional[int] = None
