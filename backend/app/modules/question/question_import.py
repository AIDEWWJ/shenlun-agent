from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.question.schemas import QuestionCreate, QuestionRead


class QuestionImportItem(QuestionCreate):
    """单个题目的导入项。"""


class QuestionImportRequest(BaseModel):
    """题库批量导入请求。"""

    items: list[QuestionImportItem] = Field(default_factory=list, min_length=1)


class QuestionImportResult(BaseModel):
    """题库批量导入结果。"""

    imported: list[QuestionRead] = Field(default_factory=list)
    failed: list[dict] = Field(default_factory=list)
