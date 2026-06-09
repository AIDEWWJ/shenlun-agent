"""题目分析能力。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.ai.capabilities.prompt_utils import render_prompt_template
from app.workflows.review.dto import QuestionAnalysisResult, ReviewLLMConfig, ReviewRequest


class QuestionAnalyzerAgent:
	"""题目分析能力。"""

	def __init__(self, llm_config: ReviewLLMConfig | None = None) -> None:
		self.llm_config = llm_config

	def analyze(self, request: ReviewRequest) -> QuestionAnalysisResult:
		if self.llm_config is None:
			raise ValueError("当前未配置可用的分析模型，请联系管理员检查配置。")

		llm_result = self._run_llm_structured(self._build_system_prompt(), self._build_prompt(request))
		if llm_result is not None:
			return llm_result
		raise RuntimeError("题目分析暂时失败，请稍后重试。")

	def _run_llm_structured(self, system_prompt: str, user_prompt: str) -> QuestionAnalysisResult | None:
		try:
			llm = ChatOpenAI(
				model=self.llm_config.model_name,
				api_key=self.llm_config.api_key,
				base_url=self.llm_config.base_url,
				temperature=self.llm_config.temperature,
			)
			structured_llm = llm.with_structured_output(QuestionAnalysisResult)
			result = structured_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
			if isinstance(result, QuestionAnalysisResult):
				return result
			return QuestionAnalysisResult.model_validate(result)
		except Exception:
			return None

	def _build_system_prompt(self) -> str:
		return (
			self.llm_config.question_analysis_system_prompt.strip()
			if self.llm_config and self.llm_config.question_analysis_system_prompt
			else ""
		)

	def _build_prompt(self, request: ReviewRequest) -> str:
		reference_points = "；".join(request.reference_points) if request.reference_points else "无"
		return render_prompt_template(
			self.llm_config.question_analysis_user_prompt if self.llm_config and self.llm_config.question_analysis_user_prompt else "",
			{
				"question_title": request.question_title,
				"question_content": request.question_content,
				"question_type": request.question_type or "未识别",
				"reference_points": reference_points,
			},
		)
