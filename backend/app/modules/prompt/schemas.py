from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PromptTemplateType = Literal[
    "review_system",
    "review_repair",
    "review_qa",
    "question_analysis_system",
    "question_analysis_user",
    "reference_point_extract_system",
    "reference_point_extract_user",
    "user_point_extract_system",
    "user_point_extract_user",
    "outline_generate_system",
    "outline_generate_user",
]


class PromptTemplateRead(BaseModel):
    id: int
    user_id: int | None = None
    name: str
    template_type: PromptTemplateType
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptTemplateListResponse(BaseModel):
    items: list[PromptTemplateRead] = Field(default_factory=list)
    total: int = 0


class PromptTemplateUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128, description="提示词名称")
    content: str = Field(min_length=1, description="提示词正文")
