"""批改工作流编排。"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from app.ai.capabilities.analyzers.question_analyzer import QuestionAnalyzerAgent
from app.ai.capabilities.comparators.point_comparator import PointComparatorAgent
from app.ai.capabilities.extractors.reference_point_extractor import ReferencePointExtractorAgent
from app.ai.capabilities.extractors.user_point_extractor import UserPointExtractorAgent
from app.ai.capabilities.generators.reviewer import ReviewerAgent
from app.ai.capabilities.runtime_config import LanguageAnalysisConfig, PointCompareConfig, StructureAnalysisConfig
from app.workflows.review.dto import (
	PointComparisonResult,
	PointExtractionResult,
	QuestionAnalysisResult,
	ReviewAnalysis,
	ReviewLLMConfig,
	ReviewPersistPayload,
	ReviewRequest,
	ReviewStep,
)


@dataclass(slots=True)
class ReviewResult:
	analysis: ReviewAnalysis
	steps: list[ReviewStep]
	persist_payload: dict[str, Any]


class ReviewService:
	"""批改工作流：题目解析 -> 要点抽取 -> 比对 -> 分析 -> 校验 -> 评分 -> 报告。"""

	def __init__(
		self,
		llm_config: ReviewLLMConfig | None = None,
		*,
		point_compare_config: PointCompareConfig | None = None,
		structure_config: StructureAnalysisConfig | None = None,
		language_config: LanguageAnalysisConfig | None = None,
	) -> None:
		self.llm_config = llm_config
		self.question_analyzer = QuestionAnalyzerAgent(llm_config)
		self.reference_point_extractor = ReferencePointExtractorAgent(llm_config)
		self.user_point_extractor = UserPointExtractorAgent(llm_config)
		self.point_comparator = PointComparatorAgent(point_compare_config)
		self.structure_config = structure_config
		self.language_config = language_config
		self.reviewer = ReviewerAgent(llm_config)

	def review(self, request: ReviewRequest) -> ReviewResult:
		if self.llm_config is None:
			raise ValueError("当前未配置可用的批改模型，请联系管理员检查配置。")

		steps: list[ReviewStep] = []
		question_analysis = self.question_analyzer.analyze(request)
		steps.append(self._step("question_analysis", "题目解析", 1, question_analysis.model_dump()))

		reference_points = self._extract_reference_points(request=request, question_analysis=question_analysis)
		steps.append(self._step("reference_point_extraction", "参考答案要点抽取", 2, reference_points.model_dump()))

		user_points = self.user_point_extractor.extract(request, question_analysis)
		steps.append(self._step("user_point_extraction", "用户答案要点抽取", 3, user_points.model_dump()))

		comparison = self.point_comparator.compare(reference_points, user_points)
		steps.append(self._step("point_comparison", "要点比对", 4, comparison.model_dump()))

		ai_analysis = self.reviewer.review(
			request,
			question_analysis=question_analysis,
			reference_point_analysis=reference_points,
			user_point_analysis=user_points,
			comparison=comparison,
		)
		steps.append(self._step("ai_review", "AI综合批改", 5, ai_analysis.model_dump()))

		analysis = self._finalize_ai_analysis(
			request=request,
			ai_analysis=ai_analysis,
			question_analysis=question_analysis,
			reference_points=reference_points,
			user_points=user_points,
			comparison=comparison,
			steps=steps,
		)
		persist_payload = ReviewPersistPayload(
			score=analysis.score,
			strengths="\n".join(analysis.strengths) if analysis.strengths else None,
			issues="\n".join(analysis.issues) if analysis.issues else None,
			suggestions="\n".join(analysis.suggestions) if analysis.suggestions else None,
			summary=analysis.summary,
		).model_dump()
		return ReviewResult(analysis=analysis, steps=steps, persist_payload=persist_payload)

	def _step(self, step_key: str, step_name: str, order_no: int, output_data: dict[str, Any]) -> ReviewStep:
		return ReviewStep(step_key=step_key, step_name=step_name, order_no=order_no, output_data=output_data)

	def _extract_reference_points(
		self,
		*,
		request: ReviewRequest,
		question_analysis: QuestionAnalysisResult,
	) -> PointExtractionResult:
		if not request.reference_points:
			return PointExtractionResult(points=[], summary="未提供参考要点，AI 将基于题干和作答直接批改")
		return self.reference_point_extractor.extract(request.reference_points, question_analysis)

	def _finalize_ai_analysis(
		self,
		*,
		request: ReviewRequest,
		ai_analysis: ReviewAnalysis,
		question_analysis: QuestionAnalysisResult,
		reference_points: PointExtractionResult,
		user_points: PointExtractionResult,
		comparison: PointComparisonResult,
		steps: list[ReviewStep],
	) -> ReviewAnalysis:
		score = min(100, max(0, ai_analysis.score))
		return ReviewAnalysis(
			score=score,
			dimensions=ai_analysis.dimensions,
			strengths=ai_analysis.strengths,
			issues=ai_analysis.issues,
			suggestions=ai_analysis.suggestions,
			summary=ai_analysis.summary,
			analysis_explanation=ai_analysis.analysis_explanation,
			outline_explanation=ai_analysis.outline_explanation,
			keyword_hits=ai_analysis.keyword_hits or list(comparison.matched_points),
			keyword_misses=ai_analysis.keyword_misses or list(comparison.missing_points),
			answer_length=len(request.answer_content),
			question_type=ai_analysis.question_type or question_analysis.question_type or request.question_type,
			question_analysis=ai_analysis.question_analysis or question_analysis.model_dump(),
			reference_point_analysis=ai_analysis.reference_point_analysis or reference_points.model_dump().get("points", []),
			user_point_analysis=ai_analysis.user_point_analysis or user_points.model_dump().get("points", []),
			comparison_analysis=ai_analysis.comparison_analysis or comparison.model_dump(),
			structure_analysis=ai_analysis.structure_analysis or {},
			language_analysis=ai_analysis.language_analysis or {},
			rule_analysis=ai_analysis.rule_analysis or {},
			score_breakdown=ai_analysis.score_breakdown,
			review_steps=[step.model_dump() for step in steps],
			report_json=ai_analysis.report_json or {},
		)



__all__ = ["ReviewService", "ReviewResult"]
