"""要点比对能力。"""

from __future__ import annotations

import re

from app.ai.capabilities.runtime_config import PointCompareConfig
from app.workflows.review.dto import PointComparisonResult, PointExtractionResult


class PointComparatorAgent:
	"""要点比对能力。"""

	def __init__(self, config: PointCompareConfig | None = None) -> None:
		self.config = config or PointCompareConfig()

	def compare(self, reference_points: PointExtractionResult, user_points: PointExtractionResult) -> PointComparisonResult:
		matched: list[str] = []
		partial: list[str] = []
		missing: list[str] = []
		extra: list[str] = []
		used_user_indexes: set[int] = set()

		for ref in reference_points.points:
			best_match = None
			best_score = 0.0
			for idx, user in enumerate(user_points.points):
				score = self._similarity(ref.text, user.text)
				if score > best_score:
					best_score = score
					best_match = idx
			if best_match is not None and best_score >= self.config.exact_match_threshold:
				matched.append(ref.text)
				used_user_indexes.add(best_match)
			elif best_match is not None and best_score >= self.config.partial_match_threshold:
				partial.append(ref.text)
				used_user_indexes.add(best_match)
			else:
				missing.append(ref.text)

		for idx, user in enumerate(user_points.points):
			if idx not in used_user_indexes:
				extra.append(user.text)

		coverage_rate = len(matched) / len(reference_points.points) if reference_points.points else 0.0
		note = f"命中 {len(matched)} 项，部分命中 {len(partial)} 项，遗漏 {len(missing)} 项。"
		return PointComparisonResult(matched_points=matched, partial_points=partial, missing_points=missing, extra_points=extra, coverage_rate=coverage_rate, note=note)

	def _similarity(self, left: str, right: str) -> float:
		if not left or not right:
			return 0.0
		if left in right or right in left:
			return 1.0
		left_tokens = set(self._extract_keywords(left))
		right_tokens = set(self._extract_keywords(right))
		if not left_tokens or not right_tokens:
			return 0.0
		intersection = len(left_tokens & right_tokens)
		union = len(left_tokens | right_tokens)
		return intersection / union if union else 0.0

	def _extract_keywords(self, text: str) -> list[str]:
		tokens = re.findall(r"[\u4e00-\u9fff]{2,}", text)
		result: list[str] = []
		for token in tokens:
			if len(token) > self.config.max_keyword_length:
				continue
			if token not in result:
				result.append(token)
		return result[: self.config.max_keywords_per_point]
