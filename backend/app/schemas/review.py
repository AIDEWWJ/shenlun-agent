from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
	"""批改请求。"""

	question_title: str = Field(min_length=1, max_length=255)
	question_content: str = Field(min_length=1)
	answer_content: str = Field(min_length=1)
	question_type: Optional[str] = Field(default=None, max_length=64)
	reference_points: list[str] = Field(default_factory=list)


class ReviewDimension(BaseModel):
	"""单项评分维度。"""

	name: str
	score: int = Field(ge=0, le=25)
	max_score: int = 25
	comment: str
	suggestions: list[str] = Field(default_factory=list)


class ReviewAnalysis(BaseModel):
	"""批改分析结果。"""

	score: int = Field(ge=0, le=100)
	dimensions: list[ReviewDimension] = Field(default_factory=list)
	strengths: list[str] = Field(default_factory=list)
	issues: list[str] = Field(default_factory=list)
	suggestions: list[str] = Field(default_factory=list)
	summary: str
	analysis_explanation: str = ""
	outline_explanation: str = ""
	keyword_hits: list[str] = Field(default_factory=list)
	keyword_misses: list[str] = Field(default_factory=list)
	answer_length: int
	question_type: Optional[str] = None


class ReviewLLMConfig(BaseModel):
	"""批改模型配置。"""

	provider: str
	model_name: str
	api_key: str
	base_url: Optional[str] = None
	temperature: float = 0.3
	system_prompt: Optional[str] = None


class ReviewPersistPayload(BaseModel):
	"""保存到 review 表的结果。"""

	score: int | None = None
	strengths: str | None = None
	issues: str | None = None
	suggestions: str | None = None
	summary: str | None = None
