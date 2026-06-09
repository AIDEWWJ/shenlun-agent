"""Legacy 批改评分与评分标准。

说明：
- 当前主批改链已切换为 AI 主评分，不再依赖本模块计算总分。
- 本模块仅保留为历史兼容 / fallback 参考，不应作为主链评分依据继续扩展。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.workflows.review.dto import LanguageAnalysisResult, PointComparisonResult, QuestionAnalysisResult, RuleValidationResult, StructureAnalysisResult


@dataclass(slots=True)
class ReviewRubricItem:
	name: str
	weight: int
	description: str


REVIEW_RUBRIC: tuple[ReviewRubricItem, ...] = (
	ReviewRubricItem(name="审题与回应", weight=10, description="题目回应与核心要求识别"),
	ReviewRubricItem(name="内容覆盖", weight=40, description="参考要点覆盖情况"),
	ReviewRubricItem(name="结构组织", weight=20, description="段落、层次与组织结构"),
	ReviewRubricItem(name="表达与语言", weight=15, description="语言规范与书面化程度"),
	ReviewRubricItem(name="规则约束", weight=15, description="硬性规则与格式约束"),
)


def calculate_score_breakdown(
	question_analysis: QuestionAnalysisResult,
	comparison: PointComparisonResult,
	structure_analysis: StructureAnalysisResult,
	language_analysis: LanguageAnalysisResult,
	rule_analysis: RuleValidationResult,
) -> dict[str, int]:
	"""计算批改分项与总分。"""

	question_score = _question_score(question_analysis, comparison)
	content_score = round(25 * comparison.coverage_rate)
	structure_score = structure_analysis.score
	language_score = language_analysis.score
	rule_score = max(0, 25 - rule_analysis.penalty)
	total_score = round(question_score * 0.1 + content_score * 0.4 + structure_score * 0.2 + language_score * 0.15 + rule_score * 0.15)
	total_score = min(100, max(0, total_score * 4))
	return {
		"question_score": question_score,
		"content_score": content_score,
		"structure_score": structure_score,
		"language_score": language_score,
		"rule_score": rule_score,
		"total_score": total_score,
	}



def _question_score(question_analysis: QuestionAnalysisResult, comparison: PointComparisonResult) -> int:
	"""审题分与回应分。"""

	base = 12
	if question_analysis.question_type:
		base += 4
	if comparison.coverage_rate >= 0.7:
		base += 6
	elif comparison.coverage_rate >= 0.4:
		base += 3
	if question_analysis.scoring_focus:
		base += min(3, len(question_analysis.scoring_focus))
	return min(25, max(0, base))
