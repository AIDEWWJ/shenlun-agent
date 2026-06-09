from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SystemConfigKey = Literal["point_compare", "structure_analysis", "language_analysis", "rule_validation", "practice_fallback"]


class SystemConfigRead(BaseModel):
    id: int
    category: str
    config_key: SystemConfigKey
    name: str
    content_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SystemConfigListResponse(BaseModel):
    items: list[SystemConfigRead] = Field(default_factory=list)
    total: int = 0


class SystemConfigUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128, description="配置名称")
    content_json: dict[str, Any] = Field(default_factory=dict, description="配置 JSON，对未传字段会按默认值补齐")
