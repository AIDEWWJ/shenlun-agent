"""批改工作流数据定义。"""

from __future__ import annotations
from typing import Any, Optional

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
	question_analysis: Optional[dict] = None
	reference_point_analysis: list[dict] = Field(default_factory=list)
	user_point_analysis: list[dict] = Field(default_factory=list)
	comparison_analysis: Optional[dict] = None
	structure_analysis: Optional[dict] = None
	language_analysis: Optional[dict] = None
	rule_analysis: Optional[dict] = None
	score_breakdown: dict[str, int] = Field(default_factory=dict)
	review_steps: list[dict] = Field(default_factory=list)
	report_json: Optional[dict] = None

class ReviewLLMConfig(BaseModel):
	"""批改模型配置。"""

	provider: str
	model_name: str
	api_key: str
	base_url: Optional[str] = None
	temperature: float = 0.3
	system_prompt: Optional[str] = None
	repair_system_prompt: Optional[str] = None
	review_system_prompt: Optional[str] = None
	review_qa_system_prompt: Optional[str] = None
	question_analysis_system_prompt: Optional[str] = None
	question_analysis_user_prompt: Optional[str] = None
	reference_point_extract_system_prompt: Optional[str] = None
	reference_point_extract_user_prompt: Optional[str] = None
	user_point_extract_system_prompt: Optional[str] = None
	user_point_extract_user_prompt: Optional[str] = None
	outline_generate_system_prompt: Optional[str] = None
	outline_generate_user_prompt: Optional[str] = None


class ReviewPersistPayload(BaseModel):
	"""保存到 review 表的结果。"""

	score: int | None = None
	strengths: str | None = None
	issues: str | None = None
	suggestions: str | None = None
	summary: str | None = None


class PointItem(BaseModel):
	"""评分点或要点项。"""

	text: str
	keywords: list[str] = Field(default_factory=list)
	weight: int = Field(default=1, ge=1, le=10)
	evidence: list[str] = Field(default_factory=list)
	matched_keywords: list[str] = Field(default_factory=list)


class QuestionAnalysisResult(BaseModel):
	"""题目解析结果。"""

	question_type: Optional[str] = None
	task_requirements: list[str] = Field(default_factory=list)
	scoring_focus: list[str] = Field(default_factory=list)
	constraints: list[str] = Field(default_factory=list)
	key_topics: list[str] = Field(default_factory=list)
	structure_hint: list[str] = Field(default_factory=list)
	note: str = ""


class PointExtractionResult(BaseModel):
	"""要点抽取结果。"""

	points: list[PointItem] = Field(default_factory=list)
	summary: str = ""


class PointComparisonResult(BaseModel):
	"""要点比对结果。"""

	matched_points: list[str] = Field(default_factory=list)
	partial_points: list[str] = Field(default_factory=list)
	missing_points: list[str] = Field(default_factory=list)
	extra_points: list[str] = Field(default_factory=list)
	coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
	note: str = ""


class StructureAnalysisResult(BaseModel):
	"""结构分析结果。"""

	score: int = Field(default=0, ge=0, le=25)
	paragraph_count: int = 0
	marker_count: int = 0
	issues: list[str] = Field(default_factory=list)
	suggestions: list[str] = Field(default_factory=list)
	note: str = ""


class LanguageAnalysisResult(BaseModel):
	"""语言分析结果。"""

	score: int = Field(default=0, ge=0, le=25)
	formal_markers: int = 0
	punctuation_hits: int = 0
	issues: list[str] = Field(default_factory=list)
	suggestions: list[str] = Field(default_factory=list)
	note: str = ""


class RuleValidationResult(BaseModel):
	"""规则校验结果。"""

	penalty: int = Field(default=0, ge=0, le=25)
	violations: list[str] = Field(default_factory=list)
	warnings: list[str] = Field(default_factory=list)
	note: str = ""


class ReviewStep(BaseModel):
	"""批改链路中的单步证据。"""

	step_key: str
	step_name: str
	order_no: int
	status: str = "success"
	critical: bool = True
	attempts: int = 1
	error: str | None = None
	input_data: dict[str, Any] = Field(default_factory=dict)
	output_data: dict[str, Any] = Field(default_factory=dict)
	note: str = ""


__all__ = [
	"ReviewRequest",
	"ReviewDimension",
	"ReviewAnalysis",
	"ReviewLLMConfig",
	"ReviewPersistPayload",
	"PointItem",
	"QuestionAnalysisResult",
	"PointExtractionResult",
	"PointComparisonResult",
	"StructureAnalysisResult",
	"LanguageAnalysisResult",
	"RuleValidationResult",
	"ReviewStep",
]
