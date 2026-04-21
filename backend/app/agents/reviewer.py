"""答案批改 Agent。

这个角色的顺序是：先批改，再讲解。
先给出分数、问题与建议，再补充题目分析和提纲解释，方便用户理解为什么这样扣分、下一步该怎么写。
当前版本仅使用 LLM 批改，不再保留规则评分兜底。
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.schemas.review import ReviewAnalysis, ReviewLLMConfig, ReviewRequest


@dataclass(slots=True)
class ReviewContext:
	"""批改上下文。"""

	question_title: str
	question_content: str
	answer_content: str
	question_type: str | None
	reference_points: list[str]


class ReviewerAgent:
	"""申论答案批改器。

	职责优先级：
	1. 先完成批改判断；
	2. 再补充分析说明；
	3. 最后给出提纲式改写方向。
	"""

	def review(self, request: ReviewRequest, llm_config: ReviewLLMConfig | None = None) -> ReviewAnalysis:
		"""执行结构化批改。"""

		if llm_config is None:
			raise ValueError("ReviewerAgent 需要提供 LLM 配置")

		context = ReviewContext(
			question_title=request.question_title.strip(),
			question_content=request.question_content.strip(),
			answer_content=request.answer_content.strip(),
			question_type=request.question_type.strip() if request.question_type else None,
			reference_points=[point.strip() for point in request.reference_points if point and point.strip()],
		)

		return self._review_with_llm(context, llm_config)

	def _review_with_llm(self, context: ReviewContext, llm_config: ReviewLLMConfig) -> ReviewAnalysis:
		"""调用 LLM 进行批改。"""

		llm = ChatOpenAI(
			model=llm_config.model_name,
			api_key=llm_config.api_key,
			base_url=llm_config.base_url,
			temperature=llm_config.temperature,
		)
		structured_llm = llm.with_structured_output(ReviewAnalysis)
		result = structured_llm.invoke(
			[
				SystemMessage(content=self.build_system_prompt(llm_config)),
				HumanMessage(content=self.build_prompt(context)),
			]
		)
		if isinstance(result, ReviewAnalysis):
			return result
		return ReviewAnalysis.model_validate(result)

	def build_system_prompt(self, llm_config: ReviewLLMConfig) -> str:
		"""生成系统提示词。"""

		base_prompt = llm_config.system_prompt.strip() if llm_config.system_prompt else ""
		return (
			f"{base_prompt}\n"
			"你是申论批改官，角色顺序必须是：先批改，再解释，再给提纲建议。"
			"先判断答案是否答到点、是否完整、是否有结构与逻辑问题；"
			"然后再解释为什么这样批改；"
			"最后给出下一版写作提纲和修改方向。"
		).strip()

	def build_prompt(self, context: ReviewContext) -> str:
		"""生成给 LLM 的提示词。"""

		reference_points = "；".join(context.reference_points) if context.reference_points else "无"

		return (
			"请严格输出符合 ReviewAnalysis 结构的内容。\n"
			"其中：\n"
			"1. score 是 0-100 的总分；\n"
			"2. dimensions 至少包含审题与回应、结构组织、内容覆盖、表达与语言四项；\n"
			"3. strengths 先写优点，issues 先写问题，suggestions 先写可执行修改建议；\n"
			"4. summary 要简洁；analysis_explanation 要解释为什么这样批改；outline_explanation 要给出下一版提纲建议。\n"
			f"题目类型：{context.question_type or '未识别'}\n"
			f"题目：{context.question_title}\n"
			f"题干：{context.question_content}\n"
			f"参考要点：{reference_points}\n"
			f"作答：{context.answer_content}\n"
			"要求：先批改，再解释，再给提纲建议。"
		)

	def to_persist_payload(self, analysis: ReviewAnalysis):
		"""把分析结果转换为可落库内容。"""

		return {
			"score": analysis.score,
			"strengths": "\n".join(analysis.strengths) if analysis.strengths else None,
			"issues": "\n".join(analysis.issues) if analysis.issues else None,
			"suggestions": "\n".join(analysis.suggestions) if analysis.suggestions else None,
			"summary": analysis.summary,
		}
