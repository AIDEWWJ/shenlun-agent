from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AiConfigBase(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    model_name: str = Field(min_length=1, max_length=128)
    api_key: str = Field(min_length=1, max_length=255)
    base_url: Optional[str] = Field(default=None, max_length=255)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    system_prompt: Optional[str] = None
    is_default: bool = False


class AiConfigCreate(AiConfigBase):
    scope: Literal["user"] = "user"


class AiConfigUpdate(BaseModel):
    provider: Optional[str] = Field(default=None, min_length=1, max_length=64)
    model_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    api_key: Optional[str] = Field(default=None, min_length=1, max_length=255)
    base_url: Optional[str] = Field(default=None, max_length=255)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    system_prompt: Optional[str] = None
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
    system_prompt: Optional[str] = None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AiConfigAdminCreate(AiConfigBase):
    scope: Literal["system"] = "system"
    user_id: Optional[int] = None


class AiConfigAdminUpdate(AiConfigUpdate):
    scope: Optional[Literal["system", "user"]] = None
    user_id: Optional[int] = None
