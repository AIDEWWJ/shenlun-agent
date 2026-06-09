"""答案批改能力。"""

from __future__ import annotations

from dataclasses import dataclass
import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.workflows.review.dto import (
	PointComparisonResult,
	PointExtractionResult,
	QuestionAnalysisResult,
	ReviewAnalysis,
	ReviewDimension,
	ReviewLLMConfig,
	ReviewRequest,
)


@dataclass(slots=True)
class ReviewContext:
	question_title: str
	question_content: str
	answer_content: str
	question_type: str | None
	reference_points: list[str]
	question_analysis: QuestionAnalysisResult | None = None
	reference_point_analysis: PointExtractionResult | None = None
	user_point_analysis: PointExtractionResult | None = None
	comparison: PointComparisonResult | None = None


class ReviewerAgent:
	"""申论答案批改器。"""

	CORE_DIMENSION_NAMES = ("审题与回应", "内容覆盖", "结构组织", "表达与语言")
	DIMENSION_ALIASES = {
		"审题": "审题与回应",
		"回应": "审题与回应",
		"内容": "内容覆盖",
		"内容覆盖度": "内容覆盖",
		"结构": "结构组织",
		"结构层次": "结构组织",
		"语言": "表达与语言",
		"表达": "表达与语言",
	}

	def __init__(self, llm_config: ReviewLLMConfig | None = None) -> None:
		self.llm_config = llm_config

	def review(
		self,
		request: ReviewRequest,
		llm_config: ReviewLLMConfig | None = None,
		*,
		question_analysis: QuestionAnalysisResult | None = None,
		reference_point_analysis: PointExtractionResult | None = None,
		user_point_analysis: PointExtractionResult | None = None,
		comparison: PointComparisonResult | None = None,
	) -> ReviewAnalysis:
		config = llm_config or self.llm_config
		if config is None:
			raise ValueError("当前未配置可用的批改模型，请联系管理员检查配置。")

		context = ReviewContext(
			question_title=request.question_title.strip(),
			question_content=request.question_content.strip(),
			answer_content=request.answer_content.strip(),
			question_type=request.question_type.strip() if request.question_type else None,
			reference_points=[point.strip() for point in request.reference_points if point and point.strip()],
			question_analysis=question_analysis,
			reference_point_analysis=reference_point_analysis,
			user_point_analysis=user_point_analysis,
			comparison=comparison,
		)

		analysis = self._review_with_llm(context, config)
		try:
			return self._stabilize_analysis(context, analysis)
		except RuntimeError as exc:
			repaired = self._repair_with_llm(context, config, analysis, str(exc))
			try:
				return self._stabilize_analysis(context, repaired)
			except RuntimeError as repair_exc:
				raise RuntimeError("批改结果整理失败，请稍后重试。") from repair_exc

	def _review_with_llm(self, context: ReviewContext, llm_config: ReviewLLMConfig) -> ReviewAnalysis:
		llm = ChatOpenAI(
			model=llm_config.model_name,
			api_key=llm_config.api_key,
			base_url=llm_config.base_url,
			temperature=llm_config.temperature,
		)
		structured_llm = llm.with_structured_output(ReviewAnalysis)
		result = structured_llm.invoke([SystemMessage(content=self.build_system_prompt(llm_config)), HumanMessage(content=self.build_prompt(context))])
		if isinstance(result, ReviewAnalysis):
			return result
		return ReviewAnalysis.model_validate(result)

	def build_system_prompt(self, llm_config: ReviewLLMConfig) -> str:
		base_prompt = (
			llm_config.review_system_prompt.strip()
			if llm_config.review_system_prompt
			else (llm_config.system_prompt.strip() if llm_config.system_prompt else "")
		)
		return (
			f"{base_prompt}\n"
			"你是申论批改官，职责是基于题目、参考要点、用户答案要点和比对证据，给出结构化 AI 批改结果。"
			"请以整体语义理解和写作质量判断为主，不要依赖固定字数阈值或僵硬规则直接打分。"
			"如果参考要点为空，也要基于题干要求和作答质量完成批改，不要因为缺少参考要点而机械判零。"
			"输出时必须先完成批改，再解释依据，最后给出下一版提纲建议。"
			"尽量填充 ReviewAnalysis 中的 comparison_analysis、structure_analysis、language_analysis、rule_analysis、score_breakdown、keyword_hits、keyword_misses。"
		).strip()

	def build_prompt(self, context: ReviewContext) -> str:
		reference_points = "；".join(context.reference_points) if context.reference_points else "无"
		question_analysis_json = json.dumps(context.question_analysis.model_dump(), ensure_ascii=False) if context.question_analysis else "{}"
		reference_point_json = (
			json.dumps(context.reference_point_analysis.model_dump(), ensure_ascii=False)
			if context.reference_point_analysis
			else "{}"
		)
		user_point_json = (
			json.dumps(context.user_point_analysis.model_dump(), ensure_ascii=False)
			if context.user_point_analysis
			else "{}"
		)
		comparison_json = json.dumps(context.comparison.model_dump(), ensure_ascii=False) if context.comparison else "{}"
		return (
			"请严格输出符合 ReviewAnalysis 结构的内容。\n"
			"其中：\n"
			"1. score 是 0-100 的总分；\n"
			"2. dimensions 必须至少包含且仅建议使用这几个核心维度名称：审题与回应、内容覆盖、结构组织、表达与语言；如有必要可额外给规则约束；\n"
			"3. strengths 先写优点，issues 先写问题，suggestions 先写可执行修改建议；\n"
			"4. summary 要简洁；analysis_explanation 要解释为什么这样批改；outline_explanation 要给出下一版提纲建议；\n"
			"5. comparison_analysis、score_breakdown 必须给出结构化结果；\n"
			"6. structure_analysis、language_analysis、rule_analysis 尽量给出结构化结果；\n"
			"7. suggestions 至少给出 2 条具体可执行建议；\n"
			"8. keyword_hits、keyword_misses 尽量对应 comparison_analysis；\n"
			"6. rule_analysis 只有在你明确识别到明显规则问题时才填写，不要机械扣分。\n"
			f"题目类型：{context.question_type or '未识别'}\n"
			f"题目：{context.question_title}\n"
			f"题干：{context.question_content}\n"
			f"参考要点：{reference_points}\n"
			f"题目解析：{question_analysis_json}\n"
			f"参考要点抽取：{reference_point_json}\n"
			f"用户要点抽取：{user_point_json}\n"
			f"要点比对结果：{comparison_json}\n"
			f"作答：{context.answer_content}\n"
			"要求：以 AI 理解为主完成批改，不要套用死规则；必须产出完整 dimensions、score_breakdown、comparison_analysis、suggestions；先批改，再解释，再给提纲建议。"
		)

	def _repair_with_llm(
		self,
		context: ReviewContext,
		llm_config: ReviewLLMConfig,
		draft_analysis: ReviewAnalysis,
		error_message: str,
	) -> ReviewAnalysis:
		llm = ChatOpenAI(
			model=llm_config.model_name,
			api_key=llm_config.api_key,
			base_url=llm_config.base_url,
			temperature=llm_config.temperature,
		)
		structured_llm = llm.with_structured_output(ReviewAnalysis)
		result = structured_llm.invoke(
			[
				SystemMessage(content=self.build_repair_system_prompt(llm_config)),
				HumanMessage(content=self.build_repair_prompt(context, draft_analysis, error_message)),
			]
		)
		if isinstance(result, ReviewAnalysis):
			return result
		return ReviewAnalysis.model_validate(result)

	def build_repair_system_prompt(self, llm_config: ReviewLLMConfig) -> str:
		base_prompt = (
			llm_config.repair_system_prompt.strip()
			if llm_config.repair_system_prompt
			else (
				llm_config.review_system_prompt.strip()
				if llm_config.review_system_prompt
				else (llm_config.system_prompt.strip() if llm_config.system_prompt else "")
			)
		)
		return (
			f"{base_prompt}\n"
			"你是申论批改结果结构化修正器。"
			"你的任务不是重新自由发挥，而是基于已有批改结果和原始批改证据，补齐缺失的结构化字段。"
			"必须优先修正 dimensions、score_breakdown、comparison_analysis、suggestions、summary、analysis_explanation。"
			"若已有字段合理，尽量保留原意，只补结构，不改批改结论方向。"
		).strip()

	def build_repair_prompt(self, context: ReviewContext, draft_analysis: ReviewAnalysis, error_message: str) -> str:
		question_analysis_json = json.dumps(context.question_analysis.model_dump(), ensure_ascii=False) if context.question_analysis else "{}"
		reference_point_json = (
			json.dumps(context.reference_point_analysis.model_dump(), ensure_ascii=False)
			if context.reference_point_analysis
			else "{}"
		)
		user_point_json = (
			json.dumps(context.user_point_analysis.model_dump(), ensure_ascii=False)
			if context.user_point_analysis
			else "{}"
		)
		comparison_json = json.dumps(context.comparison.model_dump(), ensure_ascii=False) if context.comparison else "{}"
		draft_json = draft_analysis.model_dump_json(ensure_ascii=False)
		return (
			"下面是第一次 AI 批改结果，但它的结构不完整，需要修正。\n"
			f"结构化校验失败原因：{error_message}\n"
			f"题目：{context.question_title}\n"
			f"题干：{context.question_content}\n"
			f"题目类型：{context.question_type or '未识别'}\n"
			f"题目解析：{question_analysis_json}\n"
			f"参考要点抽取：{reference_point_json}\n"
			f"用户要点抽取：{user_point_json}\n"
			f"要点比对结果：{comparison_json}\n"
			f"作答：{context.answer_content}\n"
			f"第一次 AI 批改结果：{draft_json}\n"
			"请在尽量保持原结论的前提下，输出一份完整、结构化、可直接落库的 ReviewAnalysis。"
		)

	def _stabilize_analysis(self, context: ReviewContext, analysis: ReviewAnalysis) -> ReviewAnalysis:
		normalized_dimensions = self._normalize_dimensions(analysis.dimensions)
		self._ensure_core_dimensions(normalized_dimensions)

		score_breakdown = analysis.score_breakdown or self._build_score_breakdown_from_dimensions(normalized_dimensions, analysis.score)
		if "total_score" not in score_breakdown:
			score_breakdown["total_score"] = analysis.score

		comparison_analysis = analysis.comparison_analysis or (context.comparison.model_dump() if context.comparison else None)
		if not comparison_analysis:
			raise RuntimeError("AI批改结果缺少 comparison_analysis")

		suggestions = analysis.suggestions or self._collect_dimension_suggestions(normalized_dimensions)
		if not suggestions:
			raise RuntimeError("AI批改结果缺少 suggestions")

		summary = analysis.summary.strip() if analysis.summary else ""
		if not summary:
			raise RuntimeError("AI批改结果缺少 summary")

		analysis_explanation = analysis.analysis_explanation.strip() if analysis.analysis_explanation else ""
		if not analysis_explanation:
			raise RuntimeError("AI批改结果缺少 analysis_explanation")

		question_analysis = analysis.question_analysis or (context.question_analysis.model_dump() if context.question_analysis else None)
		reference_point_analysis = analysis.reference_point_analysis or (
			context.reference_point_analysis.model_dump().get("points", []) if context.reference_point_analysis else []
		)
		user_point_analysis = analysis.user_point_analysis or (
			context.user_point_analysis.model_dump().get("points", []) if context.user_point_analysis else []
		)

		return ReviewAnalysis(
			score=min(100, max(0, analysis.score)),
			dimensions=normalized_dimensions,
			strengths=analysis.strengths,
			issues=analysis.issues,
			suggestions=suggestions,
			summary=summary,
			analysis_explanation=analysis_explanation,
			outline_explanation=analysis.outline_explanation,
			keyword_hits=analysis.keyword_hits or (context.comparison.matched_points if context.comparison else []),
			keyword_misses=analysis.keyword_misses or (context.comparison.missing_points if context.comparison else []),
			answer_length=analysis.answer_length,
			question_type=analysis.question_type or (context.question_analysis.question_type if context.question_analysis else None),
			question_analysis=question_analysis,
			reference_point_analysis=reference_point_analysis,
			user_point_analysis=user_point_analysis,
			comparison_analysis=comparison_analysis,
			structure_analysis=analysis.structure_analysis or self._dimension_to_analysis(normalized_dimensions, "结构组织"),
			language_analysis=analysis.language_analysis or self._dimension_to_analysis(normalized_dimensions, "表达与语言"),
			rule_analysis=analysis.rule_analysis or {},
			score_breakdown=score_breakdown,
			review_steps=analysis.review_steps,
			report_json=analysis.report_json or {},
		)

	def _normalize_dimensions(self, dimensions: list[ReviewDimension]) -> list[ReviewDimension]:
		normalized: list[ReviewDimension] = []
		seen: set[str] = set()
		for item in dimensions:
			name = self.DIMENSION_ALIASES.get(item.name, item.name)
			if name in seen:
				continue
			seen.add(name)
			normalized.append(
				ReviewDimension(
					name=name,
					score=min(25, max(0, item.score)),
					max_score=item.max_score,
					comment=item.comment,
					suggestions=item.suggestions,
				)
			)
		return normalized

	def _ensure_core_dimensions(self, dimensions: list[ReviewDimension]) -> None:
		existing = {item.name for item in dimensions}
		missing = [name for name in self.CORE_DIMENSION_NAMES if name not in existing]
		if missing:
			raise RuntimeError(f"AI批改结果缺少核心评分维度：{', '.join(missing)}")

	def _build_score_breakdown_from_dimensions(self, dimensions: list[ReviewDimension], total_score: int) -> dict[str, int]:
		name_map = {item.name: item.score for item in dimensions}
		return {
			"question_score": name_map.get("审题与回应", 0),
			"content_score": name_map.get("内容覆盖", 0),
			"structure_score": name_map.get("结构组织", 0),
			"language_score": name_map.get("表达与语言", 0),
			"rule_score": name_map.get("规则约束", 0),
			"total_score": total_score,
		}

	def _collect_dimension_suggestions(self, dimensions: list[ReviewDimension]) -> list[str]:
		result: list[str] = []
		for item in dimensions:
			for suggestion in item.suggestions:
				cleaned = suggestion.strip()
				if cleaned and cleaned not in result:
					result.append(cleaned)
		return result

	def _dimension_to_analysis(self, dimensions: list[ReviewDimension], name: str) -> dict:
		for item in dimensions:
			if item.name == name:
				return {
					"score": item.score,
					"issues": [item.comment] if item.comment else [],
					"suggestions": item.suggestions,
					"note": item.comment or f"{name}已由AI完成评价",
				}
		return {}

	def to_persist_payload(self, analysis: ReviewAnalysis) -> dict[str, str | None]:
		return {
			"score": analysis.score,
			"strengths": "\n".join(analysis.strengths) if analysis.strengths else None,
			"issues": "\n".join(analysis.issues) if analysis.issues else None,
			"suggestions": "\n".join(analysis.suggestions) if analysis.suggestions else None,
			"summary": analysis.summary,
		}
