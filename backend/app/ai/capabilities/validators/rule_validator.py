"""规则校验能力。"""

from __future__ import annotations

from app.ai.capabilities.runtime_config import RuleValidationConfig
from app.workflows.review.dto import PointComparisonResult, QuestionAnalysisResult, ReviewRequest, RuleValidationResult, StructureAnalysisResult


class RuleValidatorAgent:
	"""规则校验能力。"""

	def __init__(self, config: RuleValidationConfig | None = None) -> None:
		self.config = config or RuleValidationConfig()

	def validate(self, request: ReviewRequest, question_analysis: QuestionAnalysisResult, comparison: PointComparisonResult, structure_analysis: StructureAnalysisResult) -> RuleValidationResult:
		answer = request.answer_content
		penalty = 0
		violations: list[str] = []
		warnings: list[str] = []

		if len(answer) < self.config.min_answer_length:
			penalty += self.config.min_answer_penalty
			violations.append("答案过短")
		if len(answer) > self.config.max_answer_length:
			penalty += self.config.max_answer_penalty
			warnings.append("答案过长，建议适当收束")
		if comparison.coverage_rate == 0:
			penalty += self.config.zero_coverage_penalty
			violations.append("参考要点未命中")
		if question_analysis.question_type and any(
			hint in question_analysis.question_type for hint in self.config.summary_question_type_hints
		) and len(answer) > self.config.summary_question_max_length:
			penalty += self.config.summary_overlength_penalty
			warnings.append("概括类题目过度展开")
		if question_analysis.question_type and any(
			hint in question_analysis.question_type for hint in self.config.applied_doc_type_hints
		) and structure_analysis.paragraph_count < self.config.applied_doc_min_paragraphs:
			penalty += self.config.applied_doc_structure_penalty
			violations.append("应用文题结构不足")

		penalty = min(self.config.penalty_cap, penalty)
		note = "规则基本满足。" if penalty == 0 else f"存在 {len(violations)} 项明显规则问题。"
		return RuleValidationResult(penalty=penalty, violations=violations, warnings=warnings, note=note)
