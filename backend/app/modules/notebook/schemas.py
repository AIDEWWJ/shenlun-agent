"""错题本与学习计划 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ========== 错题本 ==========

class ErrorNotebookEntryRead(BaseModel):
    """错题本条目。"""

    id: int
    user_id: int
    question_id: int
    review_id: Optional[int] = None
    question_title: str
    question_type: Optional[str] = None
    score: Optional[int] = None
    error_type: str
    error_summary: Optional[str] = None
    missing_points: list[str] = Field(default_factory=list)
    weak_dimensions: list[str] = Field(default_factory=list)
    status: str
    resolve_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class ErrorNotebookListResponse(BaseModel):
    """错题本列表响应。"""

    items: list[ErrorNotebookEntryRead] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class ErrorNotebookGenerateRequest(BaseModel):
    """生成错题本请求。"""

    score_threshold: int = Field(default=60, ge=0, le=100, description="低于此分数的批改记录将被归入错题本")
    limit: int = Field(default=20, ge=1, le=100, description="最多生成条目数")


class ErrorNotebookGenerateResponse(BaseModel):
    """生成错题本响应。"""

    added: int = 0
    skipped: int = 0
    total: int = 0


class ErrorNotebookResolveRequest(BaseModel):
    """标记错题已解决。"""

    resolve_note: Optional[str] = Field(default=None, max_length=1000, description="解决备注")


# ========== 学习计划 ==========

class StudyPlanTaskItem(BaseModel):
    """学习计划任务项。"""

    day: int = Field(ge=1, description="第几天")
    question_type: Optional[str] = None
    focus: str = Field(description="训练重点")
    question_ids: list[int] = Field(default_factory=list, description="推荐题目 ID")
    target_score: Optional[int] = Field(default=None, ge=0, le=100)
    note: str = ""


class StudyPlanRead(BaseModel):
    """学习计划。"""

    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    tasks: list[StudyPlanTaskItem] = Field(default_factory=list)
    status: str
    generated_by: str
    created_at: datetime
    updated_at: datetime


class StudyPlanListResponse(BaseModel):
    """学习计划列表响应。"""

    items: list[StudyPlanRead] = Field(default_factory=list)
    total: int = 0


class StudyPlanGenerateRequest(BaseModel):
    """生成学习计划请求。"""

    days: int = Field(default=7, ge=1, le=30, description="计划天数")
    focus_types: list[str] = Field(default_factory=list, description="重点题型，为空则自动选择薄弱题型")
    use_llm: bool = Field(default=True, description="是否使用 AI 生成计划")
