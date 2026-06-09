from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.workflows.review.dto import QuestionAnalysisResult, ReviewAnalysis


class AnswerCreateRequest(BaseModel):
    """创建答案草稿。"""

    question_id: int = Field(ge=1, description="题目 ID")
    content: str = Field(min_length=1, description="答案正文")


class AnswerUpdateRequest(BaseModel):
    """更新答案草稿。"""

    content: str = Field(min_length=1, description="更新后的答案正文")


class AnswerDuplicateRequest(BaseModel):
    """复制答案版本。"""

    content: Optional[str] = Field(default=None, min_length=1, description="可选修改后的答案正文，为空则复制原内容")


class AnswerRead(BaseModel):
    id: int
    question_id: int
    user_id: int
    content: str
    version_no: int
    created_at: datetime
    question_title: Optional[str] = None
    question_type: Optional[str] = None
    reviewed: bool = False
    review_id: Optional[int] = None

    model_config = {"from_attributes": True}


class AnswerListResponse(BaseModel):
    items: list[AnswerRead] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class PracticeRecordListItem(BaseModel):
    id: int
    user_id: int
    question_id: int
    answer_id: int
    review_id: Optional[int] = None
    status: str
    is_favorite: bool = False
    created_at: datetime
    question_title: str
    question_type: Optional[str] = None
    answer_version_no: int = 1
    score: Optional[int] = None
    summary: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None


class PracticeRecordDetail(PracticeRecordListItem):
    question_content: str
    answer_content: str
    review_created_at: Optional[datetime] = None


class PracticeRecordListResponse(BaseModel):
    items: list[PracticeRecordListItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class PracticeRecordFavoriteUpdateRequest(BaseModel):
    is_favorite: bool = Field(description="是否收藏该练习记录")


class PracticeSessionCreateRequest(BaseModel):
    question_id: int = Field(ge=1, description="题目 ID")


class PracticeSessionUpdateRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict, description="当前分栏答案")
    elapsed_seconds: Optional[int] = Field(default=None, ge=0, description="累计作答秒数")


class PracticeSessionSubmitRequest(BaseModel):
    use_llm: bool = Field(default=True, description="是否使用 AI 模型执行批改")
    reference_points: list[str] = Field(default_factory=list, description="可选参考要点")


class PracticeSessionRead(BaseModel):
    id: int
    user_id: int
    question_id: int
    answer_id: Optional[int] = None
    status: str
    answers: dict[str, str] = Field(default_factory=dict)
    elapsed_seconds: int = 0
    started_at: datetime
    submitted_at: Optional[datetime] = None
    updated_at: datetime


class PracticeSessionSubmitResponse(BaseModel):
    session_id: int
    answer_id: int
    review_id: int
    status: str
    analysis: ReviewAnalysis


class ReviewExecutionResponse(BaseModel):
    answer_id: int
    review_id: int
    analysis: ReviewAnalysis


class ReviewFromContentRequest(BaseModel):
    """直接基于答案内容发起批改。"""

    question_id: int = Field(ge=1, description="题目 ID")
    answer_content: str = Field(min_length=1, description="本次提交批改的答案正文")
    answer_id: Optional[int] = Field(default=None, ge=1, description="已有答案版本 ID，可为空")
    reference_points: list[str] = Field(default_factory=list, description="可选参考要点")
    use_llm: bool = Field(default=True, description="是否使用 AI 模型执行批改")


class ReviewCreateRequest(BaseModel):
    """答案批改请求。"""

    question_id: int = Field(ge=1, description="题目 ID")
    answer_id: int = Field(ge=1, description="答案版本 ID")
    reference_points: list[str] = Field(default_factory=list, description="可选参考要点")
    use_llm: bool = Field(default=True, description="是否使用 AI 模型执行批改")
    question_title: Optional[str] = Field(default=None, max_length=255)
    question_content: Optional[str] = None
    question_type: Optional[str] = Field(default=None, max_length=64)
    answer_content: Optional[str] = None


class QuestionWorkRequest(BaseModel):
    """题目分析/提纲生成请求。"""

    question_id: int = Field(ge=1, description="题目 ID")
    reference_points: list[str] = Field(default_factory=list, description="可选参考要点")
    use_llm: bool = Field(default=True, description="是否使用 AI 模型执行分析或提纲生成")


class QuestionAnalysisResponse(BaseModel):
    question_id: int
    question_title: str
    analysis: QuestionAnalysisResult


class OutlineResponse(BaseModel):
    question_id: int
    question_title: str
    analysis: QuestionAnalysisResult
    outline: str
