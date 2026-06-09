"""结构分析能力。"""

from __future__ import annotations

import re

from app.ai.capabilities.runtime_config import StructureAnalysisConfig
from app.workflows.review.dto import PointComparisonResult, QuestionAnalysisResult, ReviewRequest, StructureAnalysisResult


class StructureAnalyzerAgent:
	"""结构分析能力。"""

	def __init__(self, config: StructureAnalysisConfig | None = None) -> None:
		self.config = config or StructureAnalysisConfig()

	def analyze(self, request: ReviewRequest, question_analysis: QuestionAnalysisResult, comparison: PointComparisonResult) -> StructureAnalysisResult:
		answer = request.answer_content
		paragraphs = [item.strip() for item in re.split(r"\n+", answer) if item.strip()]
		marker_count = sum(1 for marker in self.config.markers if marker in answer)
		bullet_count = len(re.findall(r"(?:^|\n)\s*(?:\d+[\.、]|[一二三四五六七八九十]+[\.、]|[-•])\s*", answer))
		score = self.config.base_score
		issues: list[str] = []
		suggestions: list[str] = []

		if len(paragraphs) >= self.config.min_paragraphs_for_bonus:
			score += self.config.paragraph_bonus
		else:
			issues.append("分段不够明显")
			suggestions.append("使用分段或分点增强层次")
		if marker_count >= 1:
			score += min(self.config.marker_bonus_cap, marker_count * self.config.marker_bonus_unit)
		if bullet_count >= 1:
			score += min(self.config.bullet_bonus_cap, bullet_count * self.config.bullet_bonus_unit)
		if question_analysis.question_type and any(hint in question_analysis.question_type for hint in ("贯彻执行", "应用文", "公文")):
			score += self.config.applied_doc_bonus
		if comparison.coverage_rate < self.config.low_coverage_threshold:
			issues.append("结构虽然存在，但内容覆盖不足")
			suggestions.append("先确保每个评分点都有对应位置")

		score = min(25, score)
		note = "结构较清晰。" if score >= 16 else "结构层次还需增强。"
		if not issues:
			issues.append(note)
		return StructureAnalysisResult(
			score=score,
			paragraph_count=len(paragraphs),
			marker_count=marker_count + bullet_count,
			issues=issues,
			suggestions=suggestions,
			note=note,
		)
