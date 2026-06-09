from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReviewStepRead(BaseModel):
	id: int
	review_id: int
	step_key: str
	step_name: str
	order_no: int
	status: str
	critical: bool
	attempts: int
	error: str | None = None
	input_data: dict[str, Any] = Field(default_factory=dict)
	output_data: dict[str, Any] = Field(default_factory=dict)
	note: str | None = None
	created_at: datetime


class ReviewListItem(BaseModel):
	id: int
	question_id: int
	answer_id: int
	question_title: str
	question_type: str | None = None
	score: int | None = None
	summary: str | None = None
	model_provider: str | None = None
	model_name: str | None = None
	created_at: datetime


class ReviewListResponse(BaseModel):
	items: list[ReviewListItem] = Field(default_factory=list)
	total: int = 0
	page: int = 1
	page_size: int = 20


class ReviewQARequest(BaseModel):
	question: str = Field(min_length=1, max_length=2000, description="用户当前的追问内容")
	use_llm: bool = Field(default=True, description="是否使用 AI 模型生成答疑")
	conversation_id: str | None = Field(default=None, max_length=64, description="会话 ID，连续追问时使用")
	parent_message_id: int | None = Field(default=None, ge=1, description="上一条答疑消息 ID，用于串联追问")


class ReviewRerunRequest(BaseModel):
	"""重新批改请求。"""

	reference_points: list[str] = Field(default_factory=list, description="可选参考要点，为空则复用原批改的参考要点")
	use_llm: bool = Field(default=True, description="是否使用 AI 模型执行批改")


class ReviewQAResponse(BaseModel):
	review_id: int
	question_category: str
	answer_text: str
	evidence_refs: list[str] = Field(default_factory=list)
	used_llm: bool = False


class ReviewQAMessageRead(BaseModel):
	id: int
	review_id: int
	user_id: int
	conversation_id: str
	parent_message_id: int | None = None
	round_no: int
	question_text: str
	question_category: str
	answer_text: str
	evidence_refs: list[str] = Field(default_factory=list)
	used_llm: bool = False
	created_at: datetime


class ReviewQAListResponse(BaseModel):
	items: list[ReviewQAMessageRead] = Field(default_factory=list)
	total: int = 0
	page: int = 1
	page_size: int = 20


class ReviewDetail(ReviewListItem):
	user_id: int
	question_content: str
	answer_content: str
	reference_points: list[str] = Field(default_factory=list)
	question_analysis: dict[str, Any] = Field(default_factory=dict)
	reference_point_analysis: list[dict[str, Any]] = Field(default_factory=list)
	user_point_analysis: list[dict[str, Any]] = Field(default_factory=list)
	comparison: dict[str, Any] = Field(default_factory=dict)
	structure_analysis: dict[str, Any] = Field(default_factory=dict)
	language_analysis: dict[str, Any] = Field(default_factory=dict)
	rule_analysis: dict[str, Any] = Field(default_factory=dict)
	score_breakdown: dict[str, Any] = Field(default_factory=dict)
	report: dict[str, Any] = Field(default_factory=dict)
	strengths: str | None = None
	issues: str | None = None
	suggestions: str | None = None
	steps: list[ReviewStepRead] = Field(default_factory=list)
