from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class QuestionMaterialItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    summary: str = ""
    content: str = Field(min_length=1)


class QuestionAnswerSectionItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    prompt: str = Field(min_length=1)
    word_limit_label: str = ""
    min_words: int = Field(default=0, ge=0)
    placeholder: str = ""


class QuestionBase(BaseModel):
    title: str = Field(min_length=1, max_length=255, description="题目标题")
    content: str = Field(min_length=1, description="题目正文内容")
    paper_id: Optional[int] = Field(default=None, description="所属试卷 ID")
    material: Optional[str] = Field(default=None, description="给定材料正文")
    material_refs: Optional[str] = Field(default=None, description="引用的材料编号，如 5,7")
    requirement: Optional[str] = Field(default=None, description="作答要求")
    sort_order: Optional[int] = Field(default=None, description="在试卷中的排序")
    category: Optional[str] = Field(default=None, max_length=32)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    region: Optional[str] = Field(default=None, max_length=64)
    question_type: Optional[str] = Field(default=None, max_length=64, description="题型")
    difficulty: Optional[str] = Field(default=None, max_length=32)
    theme: Optional[str] = Field(default=None, max_length=64)
    suggested_minutes: Optional[int] = Field(default=None, ge=1, le=300)
    tags: list[str] = Field(default_factory=list, description="题目标签列表")
    source: Optional[str] = Field(default=None, max_length=255, description="题目来源")
    cover_note: Optional[str] = Field(default=None, max_length=255)
    intro: Optional[str] = None
    overview: Optional[str] = None
    tasks: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)
    materials: list[QuestionMaterialItem] = Field(default_factory=list)
    answer_sections: list[QuestionAnswerSectionItem] = Field(default_factory=list)
    reference_answer: Optional[str] = None
    optimized_example: Optional[str] = None


class QuestionCreate(QuestionBase):
    scope: Optional[str] = Field(default=None, max_length=16, description="题库范围：system（管理员）/ user（个人），默认 user")


class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None, max_length=32)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    region: Optional[str] = Field(default=None, max_length=64)
    question_type: Optional[str] = Field(default=None, max_length=64)
    difficulty: Optional[str] = Field(default=None, max_length=32)
    theme: Optional[str] = Field(default=None, max_length=64)
    suggested_minutes: Optional[int] = Field(default=None, ge=1, le=300)
    tags: Optional[list[str]] = None
    source: Optional[str] = Field(default=None, max_length=255)
    cover_note: Optional[str] = Field(default=None, max_length=255)
    intro: Optional[str] = None
    overview: Optional[str] = None
    tasks: Optional[list[str]] = None
    instructions: Optional[list[str]] = None
    notices: Optional[list[str]] = None
    materials: Optional[list[QuestionMaterialItem]] = None
    answer_sections: Optional[list[QuestionAnswerSectionItem]] = None
    reference_answer: Optional[str] = None
    optimized_example: Optional[str] = None


class QuestionRead(BaseModel):
    id: int
    user_id: int
    scope: str = "user"
    title: str
    content: str
    paper_id: Optional[int] = None
    material: Optional[str] = None
    material_refs: Optional[str] = None
    requirement: Optional[str] = None
    sort_order: Optional[int] = None
    category: Optional[str] = None
    year: Optional[int] = None
    region: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    theme: Optional[str] = None
    suggested_minutes: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionDetailRead(QuestionRead):
    cover_note: Optional[str] = None
    intro: Optional[str] = None
    overview: Optional[str] = None
    tasks: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)
    materials: list[QuestionMaterialItem] = Field(default_factory=list)
    answer_sections: list[QuestionAnswerSectionItem] = Field(default_factory=list)
    reference_answer: Optional[str] = None
    optimized_example: Optional[str] = None


class QuestionWorkspaceDraft(BaseModel):
    session_id: int
    answer_id: Optional[int] = None
    status: str
    answers: dict[str, str] = Field(default_factory=dict)
    updated_at: datetime


class QuestionWorkspaceLatestReview(BaseModel):
    review_id: int
    score: Optional[int] = None
    created_at: datetime


class QuestionWorkspaceResponse(BaseModel):
    question: QuestionDetailRead
    materials: list[QuestionMaterialItem] = Field(default_factory=list)
    answer_sections: list[QuestionAnswerSectionItem] = Field(default_factory=list)
    reference_answer: Optional[str] = None
    optimized_example: Optional[str] = None
    latest_draft: Optional[QuestionWorkspaceDraft] = None
    latest_review: Optional[QuestionWorkspaceLatestReview] = None


class QuestionListResponse(BaseModel):
    items: list[QuestionRead] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    applied_filters: dict[str, str | int | None] = Field(default_factory=dict)
    applied_sort: dict[str, str] = Field(default_factory=dict)


class QuestionFilterOptionsResponse(BaseModel):
    question_types: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    sort_fields: list[Literal["created_at", "title"]] = Field(default_factory=lambda: ["created_at", "title"])
    default_sort_by: Literal["created_at"] = "created_at"
    default_sort_order: Literal["desc"] = "desc"


class QuestionImportItem(QuestionCreate):
    """单个题目的导入项。"""


class QuestionImportRequest(BaseModel):
    """题库批量导入请求。"""

    items: list[QuestionImportItem] = Field(default_factory=list, min_length=1)


class QuestionImportResult(BaseModel):
    """题库批量导入结果。"""

    imported: list[QuestionRead] = Field(default_factory=list)
    failed: list[dict] = Field(default_factory=list)
