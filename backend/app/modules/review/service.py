from __future__ import annotations

import json
import uuid
from typing import Iterable

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.modules.ai_config.service import get_effective_review_config
from app.modules.auth.repository import get_user_role_names
from app.modules.prompt.service import get_prompt_template_content
from app.modules.review.models import ReviewQAMessage
from app.modules.review.repository import (
	create_review_qa_message,
	get_review,
	get_review_qa_message,
	list_review_qa_messages as list_review_qa_messages_repo,
	list_review_steps,
	list_reviews,
)
from app.workflows.review.dto import ReviewLLMConfig
from app.modules.review.schemas import (
	ReviewDetail,
	ReviewListItem,
	ReviewListResponse,
	ReviewQAListResponse,
	ReviewQAMessageRead,
	ReviewQAResponse,
	ReviewStepRead,
)
from app.workflows.review.orchestrator import ReviewResult, ReviewService


def _is_admin(db: Session, user_id: int) -> bool:
	return "admin" in get_user_role_names(db, user_id)


def _json_loads(value: str | None, default):
	if not value:
		return default
	try:
		loaded = json.loads(value)
		return loaded if loaded is not None else default
	except Exception:
		return default


def _step_to_read(step) -> ReviewStepRead:
	return ReviewStepRead(
		id=step.id,
		review_id=step.review_id,
		step_key=step.step_key,
		step_name=step.step_name,
		order_no=step.order_no,
		status=step.status,
		critical=step.critical,
		attempts=step.attempts,
		error=step.error,
		input_data=_json_loads(step.input_json, {}),
		output_data=_json_loads(step.output_json, {}),
		note=step.note,
		created_at=step.created_at,
	)


def _review_to_list_item(review) -> ReviewListItem:
	return ReviewListItem(
		id=review.id,
		question_id=review.question_id,
		answer_id=review.answer_id,
		question_title=review.question_title_snapshot,
		question_type=review.question_type_snapshot,
		score=review.score,
		summary=review.summary,
		model_provider=review.model_provider,
		model_name=review.model_name,
		created_at=review.created_at,
	)


def _review_qa_message_to_read(message: ReviewQAMessage) -> ReviewQAMessageRead:
	return ReviewQAMessageRead(
		id=message.id,
		review_id=message.review_id,
		user_id=message.user_id,
		conversation_id=message.conversation_id,
		parent_message_id=message.parent_message_id,
		round_no=message.round_no,
		question_text=message.question_text,
		question_category=message.question_category,
		answer_text=message.answer_text,
		evidence_refs=_json_loads(message.evidence_refs_json, []),
		used_llm=message.used_llm,
		created_at=message.created_at,
	)


def _compact_lines(values: Iterable[str | None]) -> list[str]:
	lines: list[str] = []
	for value in values:
		if not value:
			continue
		for item in str(value).splitlines():
			cleaned = item.strip()
			if cleaned:
				lines.append(cleaned)
	return lines


def _truncate_lines(lines: list[str], limit: int = 3) -> list[str]:
	return lines[:limit]


def _classify_review_question(question: str) -> str:
	text = question.strip()
	if any(keyword in text for keyword in ["为什么扣", "扣分", "分数", "得分"]):
		return "score_explanation"
	if any(keyword in text for keyword in ["要点", "漏答", "没写到", "命中"]):
		return "point_explanation"
	if any(keyword in text for keyword in ["结构", "层次", "分段", "逻辑"]):
		return "structure_explanation"
	if any(keyword in text for keyword in ["语言", "表达", "病句", "错别字", "书面"]):
		return "language_explanation"
	if any(keyword in text for keyword in ["规则", "字数", "跑题", "格式"]):
		return "rule_explanation"
	if any(keyword in text for keyword in ["怎么改", "如何改", "改写", "优化", "重写"]):
		return "rewrite_suggestion"
	return "general_followup"


def _build_review_qa_fallback(detail: ReviewDetail, question: str) -> ReviewQAResponse:
	category = _classify_review_question(question)
	evidence_refs: list[str] = []

	score_breakdown = detail.score_breakdown or {}
	comparison = detail.comparison or {}
	structure_analysis = detail.structure_analysis or {}
	language_analysis = detail.language_analysis or {}
	rule_analysis = detail.rule_analysis or {}

	if category == "score_explanation":
		parts = [
			f"这次总分为 {detail.score if detail.score is not None else '未评分'} 分。",
			f"审题与回应 {score_breakdown.get('question_score', 0)} 分，内容覆盖 {score_breakdown.get('content_score', 0)} 分，结构组织 {score_breakdown.get('structure_score', 0)} 分，表达与语言 {score_breakdown.get('language_score', 0)} 分，规则约束 {score_breakdown.get('rule_score', 0)} 分。",
		]
		evidence_refs.append("score_breakdown")
		missing_points = comparison.get("missing_points") or []
		if missing_points:
			parts.append(f"主要失分点集中在漏掉的要点，例如：{'；'.join(missing_points[:3])}。")
			evidence_refs.append("comparison.missing_points")
		answer_text = " ".join(parts)
	elif category == "point_explanation":
		matched_points = comparison.get("matched_points") or []
		missing_points = comparison.get("missing_points") or []
		parts = []
		if matched_points:
			parts.append(f"你已经命中的要点包括：{'；'.join(matched_points[:3])}。")
			evidence_refs.append("comparison.matched_points")
		if missing_points:
			parts.append(f"漏答要点包括：{'；'.join(missing_points[:3])}。")
			evidence_refs.append("comparison.missing_points")
		if not parts:
			parts.append("当前批改结果里没有明显的要点命中或漏答证据。")
		answer_text = " ".join(parts)
	elif category == "structure_explanation":
		issues = _truncate_lines(_compact_lines(structure_analysis.get("issues", [])))
		suggestions = _truncate_lines(_compact_lines(structure_analysis.get("suggestions", [])))
		parts = [f"结构维度得分为 {score_breakdown.get('structure_score', 0)} 分。"]
		if issues:
			parts.append(f"结构问题主要在：{'；'.join(issues)}。")
			evidence_refs.append("structure_analysis.issues")
		if suggestions:
			parts.append(f"建议优先按这些方向调整：{'；'.join(suggestions)}。")
			evidence_refs.append("structure_analysis.suggestions")
		answer_text = " ".join(parts)
	elif category == "language_explanation":
		issues = _truncate_lines(_compact_lines(language_analysis.get("issues", [])))
		suggestions = _truncate_lines(_compact_lines(language_analysis.get("suggestions", [])))
		parts = [f"语言表达维度得分为 {score_breakdown.get('language_score', 0)} 分。"]
		if issues:
			parts.append(f"主要语言问题有：{'；'.join(issues)}。")
			evidence_refs.append("language_analysis.issues")
		if suggestions:
			parts.append(f"可优先这样改：{'；'.join(suggestions)}。")
			evidence_refs.append("language_analysis.suggestions")
		answer_text = " ".join(parts)
	elif category == "rule_explanation":
		violations = _truncate_lines(_compact_lines(rule_analysis.get("violations", [])))
		warnings = _truncate_lines(_compact_lines(rule_analysis.get("warnings", [])))
		parts = [f"规则约束维度得分为 {score_breakdown.get('rule_score', 0)} 分。"]
		if violations:
			parts.append(f"明确触发的规则问题有：{'；'.join(violations)}。")
			evidence_refs.append("rule_analysis.violations")
		if warnings:
			parts.append(f"补充提醒包括：{'；'.join(warnings)}。")
			evidence_refs.append("rule_analysis.warnings")
		answer_text = " ".join(parts)
	elif category == "rewrite_suggestion":
		suggestions = _truncate_lines(_compact_lines([detail.suggestions]))
		outline = detail.report.get("outline") if detail.report else None
		parts = []
		if suggestions:
			parts.append(f"优先修改这些问题：{'；'.join(suggestions)}。")
			evidence_refs.append("suggestions")
		if outline:
			parts.append(f"下一版可参考这个结构提纲：{outline}。")
			evidence_refs.append("report.outline")
		if not parts:
			parts.append("建议先补齐漏答要点，再优化结构和语言表达。")
		answer_text = " ".join(parts)
	elif category == "general_followup":
		parts = []
		if detail.summary:
			parts.append(f"这次批改的总体结论是：{detail.summary}")
			evidence_refs.append("summary")
		if detail.issues:
			parts.append(f"当前最需要优先解决的问题是：{'；'.join(_truncate_lines(_compact_lines([detail.issues])))}。")
			evidence_refs.append("issues")
		if detail.suggestions:
			parts.append(f"对应建议是：{'；'.join(_truncate_lines(_compact_lines([detail.suggestions])))}。")
			evidence_refs.append("suggestions")
		if not parts:
			parts.append("当前批改信息不足以给出更具体解释，建议结合完整报告继续查看。")
		answer_text = " ".join(parts)
	else:
		answer_text = "当前问题暂未命中专门的解释类型，建议结合完整批改报告继续查看。"

	return ReviewQAResponse(
		review_id=detail.id,
		question_category=category,
		answer_text=answer_text,
		evidence_refs=evidence_refs,
		used_llm=False,
	)


def _build_review_qa_llm_answer(
	detail: ReviewDetail,
	question: str,
	conversation_history: list[ReviewQAMessageRead],
	llm_config: ReviewLLMConfig,
) -> ReviewQAResponse | None:
	try:
		category = _classify_review_question(question)
		history_lines: list[str] = []
		for item in conversation_history[-5:]:
			history_lines.append(f"第{item.round_no}轮用户问题：{item.question_text}")
			history_lines.append(f"第{item.round_no}轮系统回答：{item.answer_text}")
		history_text = "\n".join(history_lines) if history_lines else "无历史对话"

		evidence_lines = [
			f"总评：{detail.summary or '无'}",
			f"总分：{detail.score if detail.score is not None else '未评分'}",
			f"分数拆解：{json.dumps(detail.score_breakdown, ensure_ascii=False)}",
			f"要点对比：{json.dumps(detail.comparison, ensure_ascii=False)}",
			f"结构分析：{json.dumps(detail.structure_analysis, ensure_ascii=False)}",
			f"语言分析：{json.dumps(detail.language_analysis, ensure_ascii=False)}",
			f"规则分析：{json.dumps(detail.rule_analysis, ensure_ascii=False)}",
			f"修改建议：{detail.suggestions or '无'}",
		]
		base_prompt = (
			llm_config.review_qa_system_prompt.strip()
			if llm_config.review_qa_system_prompt
			else (
				llm_config.review_system_prompt.strip()
				if llm_config.review_system_prompt
				else (llm_config.system_prompt.strip() if llm_config.system_prompt else "")
			)
		)
		system_prompt = (
			f"{base_prompt}\n"
			"如果用户在追问上一轮，请结合历史对话连续回答。"
		).strip()
		user_prompt = (
			f"问题分类：{category}\n"
			f"历史对话：\n{history_text}\n\n"
			f"批改证据：\n" + "\n".join(evidence_lines) + "\n\n"
			f"当前用户问题：{question}\n"
			"请给出简洁明确的答复。"
		)
		llm = ChatOpenAI(
			model=llm_config.model_name,
			api_key=llm_config.api_key,
			base_url=llm_config.base_url,
			temperature=llm_config.temperature,
		)
		result = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
		answer_text = str(result.content).strip() if result and result.content else ""
		if not answer_text:
			return None
		return ReviewQAResponse(
			review_id=detail.id,
			question_category=category,
			answer_text=answer_text,
			evidence_refs=["summary", "score_breakdown", "comparison", "structure_analysis", "language_analysis", "rule_analysis", "suggestions"],
			used_llm=True,
		)
	except Exception:
		return None


def get_review_detail(db: Session, *, review_id: int, current_user_id: int) -> ReviewDetail:
	review = get_review(db, review_id)
	if review is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="批改记录不存在")
	if review.user_id != current_user_id and not _is_admin(db, current_user_id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该批改记录")
	steps = list_review_steps(db, review.id)
	return ReviewDetail(
		**_review_to_list_item(review).model_dump(),
		user_id=review.user_id,
		question_content=review.question_content_snapshot,
		answer_content=review.answer_content_snapshot,
		reference_points=_json_loads(review.reference_points_json, []),
		question_analysis=_json_loads(review.question_analysis_json, {}),
		reference_point_analysis=_json_loads(review.reference_point_analysis_json, []),
		user_point_analysis=_json_loads(review.user_point_analysis_json, []),
		comparison=_json_loads(review.comparison_json, {}),
		structure_analysis=_json_loads(review.structure_analysis_json, {}),
		language_analysis=_json_loads(review.language_analysis_json, {}),
		rule_analysis=_json_loads(review.rule_analysis_json, {}),
		score_breakdown=_json_loads(review.score_breakdown_json, {}),
		report=_json_loads(review.report_json, {}),
		strengths=review.strengths,
		issues=review.issues,
		suggestions=review.suggestions,
		steps=[_step_to_read(step) for step in steps],
	)


def _ensure_review_access(db: Session, *, review_id: int, current_user_id: int):
	review = get_review(db, review_id)
	if review is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="批改记录不存在")
	if review.user_id != current_user_id and not _is_admin(db, current_user_id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该批改记录")
	return review


def list_my_reviews(
	db: Session,
	*,
	current_user_id: int,
	page: int = 1,
	page_size: int = 20,
	question_id: int | None = None,
	question_type: str | None = None,
) -> ReviewListResponse:
	items, total = list_reviews(
		db,
		user_id=current_user_id,
		question_id=question_id,
		question_type=question_type,
		page=page,
		page_size=page_size,
	)
	return ReviewListResponse(
		items=[_review_to_list_item(item) for item in items],
		total=total,
		page=page,
		page_size=page_size,
	)


def answer_review_question(
	db: Session,
	*,
	review_id: int,
	current_user_id: int,
	question: str,
	use_llm: bool = True,
	conversation_id: str | None = None,
	parent_message_id: int | None = None,
) -> ReviewQAMessageRead:
	detail = get_review_detail(db, review_id=review_id, current_user_id=current_user_id)
	parent_message = None
	if parent_message_id is not None:
		parent_message = get_review_qa_message(db, parent_message_id)
		if parent_message is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="父答疑消息不存在")
		if parent_message.review_id != review_id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父答疑消息不属于该批改记录")
		if parent_message.user_id != current_user_id and not _is_admin(db, current_user_id):
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权引用该答疑消息")

	if conversation_id is None:
		conversation_id = parent_message.conversation_id if parent_message is not None else uuid.uuid4().hex
	elif parent_message is not None and conversation_id != parent_message.conversation_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话 ID 与父答疑消息不一致")

	history, total = list_review_qa_messages_repo(
		db,
		review_id=review_id,
		user_id=None if _is_admin(db, current_user_id) else current_user_id,
		conversation_id=conversation_id,
		page=1,
		page_size=200,
	)
	history_reads = [_review_qa_message_to_read(item) for item in history]
	round_no = total + 1
	llm_config = None
	if use_llm:
		config = get_effective_review_config(db, current_user_id)
		if config is not None:
			llm_config = ReviewLLMConfig(
				provider=config.provider,
				model_name=config.model_name,
				api_key=config.api_key,
				base_url=config.base_url,
				temperature=config.temperature,
				system_prompt=config.system_prompt,
				repair_system_prompt=get_prompt_template_content(db, "review_repair"),
				review_system_prompt=get_prompt_template_content(db, "review_system"),
				review_qa_system_prompt=get_prompt_template_content(db, "review_qa"),
			)
	response = None
	if use_llm and llm_config is not None:
		response = _build_review_qa_llm_answer(detail, question, history_reads, llm_config)
	if response is None:
		response = _build_review_qa_fallback(detail, question)
	message = create_review_qa_message(
		db,
		ReviewQAMessage(
			review_id=review_id,
			user_id=current_user_id,
			conversation_id=conversation_id,
			parent_message_id=parent_message_id,
			round_no=round_no,
			question_text=question,
			question_category=response.question_category,
			answer_text=response.answer_text,
			evidence_refs_json=json.dumps(response.evidence_refs, ensure_ascii=False),
			used_llm=response.used_llm,
		),
	)
	db.commit()
	db.refresh(message)
	return _review_qa_message_to_read(message)


def list_review_qa_messages(
	db: Session,
	*,
	review_id: int,
	current_user_id: int,
	conversation_id: str | None = None,
	page: int = 1,
	page_size: int = 20,
) -> ReviewQAListResponse:
	_ensure_review_access(db, review_id=review_id, current_user_id=current_user_id)
	user_filter = None if _is_admin(db, current_user_id) else current_user_id
	items, total = list_review_qa_messages_repo(
		db,
		review_id=review_id,
		user_id=user_filter,
		conversation_id=conversation_id,
		page=page,
		page_size=page_size,
	)
	return ReviewQAListResponse(
		items=[_review_qa_message_to_read(item) for item in items],
		total=total,
		page=page,
		page_size=page_size,
	)


def rerun_review(
	db: Session,
	*,
	review_id: int,
	current_user_id: int,
	reference_points: list[str] | None = None,
	use_llm: bool = True,
):
	"""对同一答案重新发起批改。"""
	review = get_review(db, review_id)
	if review is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="批改记录不存在")
	if review.user_id != current_user_id and not _is_admin(db, current_user_id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该批改记录")

	# 复用原批改的参考要点（如果未传入新的）
	if not reference_points:
		reference_points = _json_loads(review.reference_points_json, [])

	from app.modules.practice.service import review_answer_from_content

	return review_answer_from_content(
		db,
		user_id=current_user_id,
		question_id=review.question_id,
		answer_content=review.answer_content_snapshot,
		answer_id=None,
		reference_points=reference_points,
		use_llm=use_llm,
	)


__all__ = [
	"ReviewService",
	"ReviewResult",
	"answer_review_question",
	"get_review_detail",
	"list_review_qa_messages",
	"list_my_reviews",
	"rerun_review",
]
