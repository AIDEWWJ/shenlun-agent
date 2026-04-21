"""练习业务层。

这里放题目分析、提纲生成、答案批改等业务逻辑。
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents.reviewer import ReviewerAgent
from app.repositories.practice_repo import create_practice_record, create_review, get_answer, get_question, get_review_by_answer_id
from app.schemas.review import ReviewAnalysis, ReviewLLMConfig, ReviewRequest
from app.services.ai_config_service import get_effective_review_config


def review_answer(
	db: Session,
	*,
	user_id: int,
	question_id: int,
	answer_id: int,
	reference_points: list[str] | None = None,
	use_llm: bool = True,
) -> ReviewAnalysis:
	"""对用户答案执行批改并保存 review 记录。"""

	question = get_question(db, question_id)
	if question is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

	answer = get_answer(db, answer_id)
	if answer is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="答案不存在")

	if answer.user_id != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能批改他人的答案")
	if answer.question_id != question_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="答案不属于该题目")

	agent = ReviewerAgent()
	llm_config = None
	if use_llm:
		config = get_effective_review_config(db, user_id)
		if config is None:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未配置可用于批改的 AI 模型，请先设置默认配置")
		llm_config = ReviewLLMConfig(
			provider=config.provider,
			model_name=config.model_name,
			api_key=config.api_key,
			base_url=config.base_url,
			temperature=config.temperature,
			system_prompt=config.system_prompt,
		)
	request = ReviewRequest(
		question_title=question.title,
		question_content=question.content,
		answer_content=answer.content,
		question_type=question.question_type,
		reference_points=reference_points or [],
	)
	analysis = agent.review(request, llm_config)
	payload = agent.to_persist_payload(analysis)

	existing_review = get_review_by_answer_id(db, answer.id)
	if existing_review is None:
		review = create_review(db, answer_id=answer.id, **payload)
	else:
		existing_review.score = payload["score"]
		existing_review.strengths = payload["strengths"]
		existing_review.issues = payload["issues"]
		existing_review.suggestions = payload["suggestions"]
		existing_review.summary = payload["summary"]
		db.flush()
		review = existing_review

	create_practice_record(db, user_id=user_id, question_id=question.id, answer_id=answer.id, review_id=review.id)
	db.commit()
	return analysis
