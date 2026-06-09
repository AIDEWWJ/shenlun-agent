"""参考答案要点抽取能力。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.ai.capabilities.prompt_utils import render_prompt_template
from app.workflows.review.dto import PointExtractionResult, QuestionAnalysisResult, ReviewLLMConfig


class ReferencePointExtractorAgent:
	"""参考答案要点抽取能力。"""

	def __init__(self, llm_config: ReviewLLMConfig | None = None) -> None:
		self.llm_config = llm_config

	def extract(self, reference_points: list[str], question_analysis: QuestionAnalysisResult | None = None) -> PointExtractionResult:
		if self.llm_config is None:
			raise ValueError("当前未配置可用的批改模型，请联系管理员检查配置。")

		llm_result = self._run_llm(reference_points, question_analysis)
		if llm_result is not None:
			return llm_result
		raise RuntimeError("参考要点整理暂时失败，请稍后重试。")

	def _run_llm(self, reference_points: list[str], question_analysis: QuestionAnalysisResult | None) -> PointExtractionResult | None:
		try:
			llm = ChatOpenAI(
				model=self.llm_config.model_name,
				api_key=self.llm_config.api_key,
				base_url=self.llm_config.base_url,
				temperature=self.llm_config.temperature,
			)
			structured_llm = llm.with_structured_output(PointExtractionResult)
			result = structured_llm.invoke([
				SystemMessage(content=self._build_system_prompt()),
				HumanMessage(content=self._build_prompt(reference_points, question_analysis)),
			])
			if isinstance(result, PointExtractionResult):
				return result
			return PointExtractionResult.model_validate(result)
		except Exception:
			return None

	def _build_system_prompt(self) -> str:
		return (
			self.llm_config.reference_point_extract_system_prompt.strip()
			if self.llm_config and self.llm_config.reference_point_extract_system_prompt
			else ""
		)

	def _build_prompt(self, reference_points: list[str], question_analysis: QuestionAnalysisResult | None) -> str:
		reference_points_text = "\n".join(f"{index}. {item}" for index, item in enumerate(reference_points, start=1)) or "无"
		return render_prompt_template(
			self.llm_config.reference_point_extract_user_prompt if self.llm_config and self.llm_config.reference_point_extract_user_prompt else "",
			{
				"reference_points_text": reference_points_text,
				"question_type": question_analysis.question_type if question_analysis and question_analysis.question_type else "未识别",
				"scoring_focus": "、".join(question_analysis.scoring_focus) if question_analysis and question_analysis.scoring_focus else "无",
				"question_analysis_json": question_analysis.model_dump_json() if question_analysis else "{}",
			},
		)
