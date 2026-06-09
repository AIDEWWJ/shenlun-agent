"""Dashboard 数据模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecentPracticeItem(BaseModel):
    """最近练习条目。"""

    record_id: int
    question_id: int
    question_title: str
    question_type: Optional[str] = None
    score: Optional[int] = None
    created_at: datetime


class DashboardResponse(BaseModel):
    """用户学习概览。"""

    total_practices: int = 0
    total_reviews: int = 0
    avg_score: Optional[float] = None
    latest_score: Optional[int] = None
    best_score: Optional[int] = None
    streak_days: int = 0
    weak_question_types: list[str] = Field(default_factory=list)
    recent_items: list[RecentPracticeItem] = Field(default_factory=list)


class QuestionTypeStats(BaseModel):
    """按题型统计。"""

    question_type: str
    count: int = 0
    avg_score: Optional[float] = None
    best_score: Optional[int] = None
    latest_score: Optional[int] = None


class StatsResponse(BaseModel):
    """统计响应。"""

    items: list[QuestionTypeStats] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    """推荐题目条目。"""

    question_id: int
    title: str
    question_type: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    reason: str


class RecommendationResponse(BaseModel):
    """推荐题目响应。"""

    items: list[RecommendationItem] = Field(default_factory=list)


class TrendItem(BaseModel):
    """趋势数据点。"""

    date: str
    count: int = 0
    avg_score: Optional[float] = None


class TrendResponse(BaseModel):
    """趋势响应。"""

    items: list[TrendItem] = Field(default_factory=list)


class ReviewCompareResponse(BaseModel):
    """批改对比响应。"""

    base_review_id: int
    target_review_id: int
    score_diff: int = 0
    base_score: Optional[int] = None
    target_score: Optional[int] = None
    dimension_diffs: list[dict] = Field(default_factory=list)
    issues_added: list[str] = Field(default_factory=list)
    issues_resolved: list[str] = Field(default_factory=list)
    suggestion_changes: list[str] = Field(default_factory=list)
