"""提纲生成能力。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.ai.capabilities.prompt_utils import render_prompt_template
from app.workflows.review.dto import PointComparisonResult, QuestionAnalysisResult, ReviewLLMConfig


class OutlineGeneratorAgent:
	"""提纲生成能力。"""

	def __init__(self, llm_config: ReviewLLMConfig | None = None) -> None:
		self.llm_config = llm_config

	def generate(self, question_analysis: QuestionAnalysisResult, comparison: PointComparisonResult) -> str:
		if self.llm_config is None:
			raise ValueError("当前未配置可用的提纲模型，请联系管理员检查配置。")
		llm_result = self._run_llm(question_analysis, comparison)
		if llm_result is not None:
			return llm_result
		raise RuntimeError("提纲生成暂时失败，请稍后重试。")

	def _run_llm(self, question_analysis: QuestionAnalysisResult, comparison: PointComparisonResult) -> str | None:
		try:
			llm = ChatOpenAI(
				model=self.llm_config.model_name,
				api_key=self.llm_config.api_key,
				base_url=self.llm_config.base_url,
				temperature=self.llm_config.temperature,
			)
			result = llm.invoke([SystemMessage(content=self._build_system_prompt()), HumanMessage(content=self._build_prompt(question_analysis, comparison))])
			return getattr(result, "content", None) or str(result)
		except Exception:
			return None

	def _build_system_prompt(self) -> str:
		return (
			self.llm_config.outline_generate_system_prompt.strip()
			if self.llm_config and self.llm_config.outline_generate_system_prompt
			else ""
		)

	def _build_prompt(self, question_analysis: QuestionAnalysisResult, comparison: PointComparisonResult) -> str:
		return render_prompt_template(
			self.llm_config.outline_generate_user_prompt if self.llm_config and self.llm_config.outline_generate_user_prompt else "",
			{
				"question_type": question_analysis.question_type or "未识别",
				"scoring_focus": "、".join(question_analysis.scoring_focus) if question_analysis.scoring_focus else "无",
				"missing_points": "、".join(comparison.missing_points) if comparison.missing_points else "无",
				"matched_points": "、".join(comparison.matched_points) if comparison.matched_points else "无",
				"question_analysis_json": question_analysis.model_dump_json(),
				"comparison_json": comparison.model_dump_json(),
			},
		)
