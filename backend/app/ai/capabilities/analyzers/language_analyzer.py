"""语言分析能力。"""

from __future__ import annotations

from app.ai.capabilities.runtime_config import LanguageAnalysisConfig
from app.workflows.review.dto import LanguageAnalysisResult, ReviewRequest


class LanguageAnalyzerAgent:
	"""语言分析能力。"""

	def __init__(self, config: LanguageAnalysisConfig | None = None) -> None:
		self.config = config or LanguageAnalysisConfig()

	def analyze(self, request: ReviewRequest) -> LanguageAnalysisResult:
		answer = request.answer_content
		paragraphs = [item.strip() for item in answer.splitlines() if item.strip()]
		punctuation_hits = sum(answer.count(symbol) for symbol in self.config.punctuation_targets)
		formal_markers = sum(1 for marker in self.config.formal_markers if marker in answer)
		score = self.config.base_score
		issues: list[str] = []
		suggestions: list[str] = []

		if punctuation_hits >= self.config.punctuation_threshold:
			score += self.config.punctuation_bonus
		else:
			issues.append("标点与句式展开略少")
			suggestions.append("适当增加分句和连接词")
		if formal_markers >= self.config.formal_marker_threshold:
			score += min(self.config.formal_marker_bonus_cap, formal_markers * self.config.formal_marker_bonus_unit)
		if len(paragraphs) >= self.config.min_paragraphs_for_bonus:
			score += self.config.paragraph_bonus
		if len(answer) < self.config.short_answer_threshold:
			score -= self.config.short_answer_penalty
			issues.append("表达偏短")
			issues.append("展开不够充分")
			suggestions.append("补充解释和论证")

		score = min(25, max(0, score))
		note = "表达较规范。" if score >= 15 else "表达还可以更凝练。"
		if not issues:
			issues.append(note)
		return LanguageAnalysisResult(
			score=score,
			formal_markers=formal_markers,
			punctuation_hits=punctuation_hits,
			issues=issues,
			suggestions=suggestions,
			note=note,
		)
