"""题库业务模块。"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.auth.repository import get_user_role_names
from app.modules.practice.repository import get_current_practice_session_by_question, get_latest_review_for_question
from app.modules.question.models import Question
from app.modules.question.repository import (
	create_question,
	delete_question,
	get_question,
	list_question_filter_values,
	list_questions,
	update_question,
)
from app.modules.question.schemas import (
	QuestionCreate,
	QuestionDetailRead,
	QuestionFilterOptionsResponse,
	QuestionImportRequest,
	QuestionImportResult,
	QuestionListResponse,
	QuestionRead,
	QuestionUpdate,
	QuestionWorkspaceDraft,
	QuestionWorkspaceLatestReview,
	QuestionWorkspaceResponse,
)


def _is_admin(db: Session, user_id: int) -> bool:
	return "admin" in get_user_role_names(db, user_id)


def _normalize_tags(tags: list[str] | None) -> str | None:
	if not tags:
		return None
	cleaned = [item.strip() for item in tags if item and item.strip()]
	return ",".join(dict.fromkeys(cleaned)) or None


def _split_tags(tags: str | None) -> list[str]:
	if not tags:
		return []
	return [item.strip() for item in tags.split(",") if item.strip()]


def _json_dumps(value: Any) -> str | None:
	if value is None:
		return None
	return json.dumps(value, ensure_ascii=False)


def _json_loads(value: str | None, default):
	if not value:
		return default
	try:
		loaded = json.loads(value)
		return loaded if loaded is not None else default
	except Exception:
		return default


def _serialize_question_payload(data: dict[str, Any]) -> dict[str, Any]:
	payload = dict(data)
	if "tags" in payload:
		payload["tags"] = _normalize_tags(payload["tags"])
	if "tasks" in payload:
		payload["tasks_json"] = _json_dumps(payload.pop("tasks"))
	if "instructions" in payload:
		payload["instructions_json"] = _json_dumps(payload.pop("instructions"))
	if "notices" in payload:
		payload["notices_json"] = _json_dumps(payload.pop("notices"))
	if "materials" in payload:
		payload["materials_json"] = _json_dumps(payload.pop("materials"))
	if "answer_sections" in payload:
		payload["answer_sections_json"] = _json_dumps(payload.pop("answer_sections"))
	return payload


def _to_read_model(question: Question) -> QuestionRead:
	return QuestionRead(
		id=question.id,
		user_id=question.user_id,
		scope=question.scope or "user",
		title=question.title,
		content=question.content,
		paper_id=question.paper_id,
		material=question.material,
		material_refs=question.material_refs,
		requirement=question.requirement,
		sort_order=question.sort_order,
		category=question.category,
		year=question.year,
		region=question.region,
		question_type=question.question_type,
		difficulty=question.difficulty,
		theme=question.theme,
		suggested_minutes=question.suggested_minutes,
		tags=_split_tags(question.tags),
		source=question.source,
		created_at=question.created_at,
	)


def _to_detail_read_model(question: Question) -> QuestionDetailRead:
	base = _to_read_model(question).model_dump()
	return QuestionDetailRead(
		**base,
		cover_note=question.cover_note,
		intro=question.intro,
		overview=question.overview,
		tasks=_json_loads(question.tasks_json, []),
		instructions=_json_loads(question.instructions_json, []),
		notices=_json_loads(question.notices_json, []),
		materials=_json_loads(question.materials_json, []),
		answer_sections=_json_loads(question.answer_sections_json, []),
		reference_answer=question.reference_answer,
		optimized_example=question.optimized_example,
	)


def list_question_bank(
	db: Session,
	current_user: User,
	*,
	page: int = 1,
	page_size: int = 20,
	paper_id: int | None = None,
	keyword: str | None = None,
	question_type: str | None = None,
	tag: str | None = None,
	source: str | None = None,
	user_id: int | None = None,
	scope: str | None = None,
	sort_by: str = "created_at",
	sort_order: str = "desc",
) -> QuestionListResponse:
	is_admin = _is_admin(db, current_user.id)
	if user_id is not None and not is_admin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可按用户筛选题库")
	if sort_by not in {"created_at", "title"}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的排序字段")
	if sort_order not in {"asc", "desc"}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的排序方向")

	# 确定查询范围
	# 管理员：可按 user_id/scope 自由筛选，默认看全部
	# 普通用户：看 scope=system 的全部 + 自己 scope=user 的
	if is_admin:
		owner_id = user_id  # None 表示不限
		query_scope = scope  # None 表示不限
	else:
		owner_id = current_user.id
		query_scope = scope  # 前端可传 system/user/None

	items, total = list_questions(
		db,
		user_id=owner_id,
		scope=query_scope,
		include_system=not is_admin,  # 普通用户额外包含系统题库
		paper_id=paper_id,
		keyword=keyword,
		question_type=question_type,
		tag=tag,
		source=source,
		sort_by=sort_by,
		sort_order=sort_order,
		page=page,
		page_size=page_size,
	)
	return QuestionListResponse(
		items=[_to_read_model(item) for item in items],
		total=total,
		page=page,
		page_size=page_size,
		applied_filters={
			"keyword": keyword,
			"question_type": question_type,
			"tag": tag,
			"source": source,
			"user_id": owner_id,
			"scope": query_scope,
		},
		applied_sort={"sort_by": sort_by, "sort_order": sort_order},
	)


def get_question_detail(db: Session, current_user: User, question_id: int) -> QuestionDetailRead:
	question = get_question(db, question_id)
	if question is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
	# 系统题库所有人可看；个人题库只有本人和管理员可看
	if question.scope != "system" and question.user_id != current_user.id and not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该题目")
	return _to_detail_read_model(question)


def get_question_workspace(db: Session, current_user: User, question_id: int) -> QuestionWorkspaceResponse:
	question = get_question(db, question_id)
	if question is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
	if question.scope != "system" and question.user_id != current_user.id and not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该题目")

	detail = _to_detail_read_model(question)
	current_session = get_current_practice_session_by_question(db, user_id=current_user.id, question_id=question.id)
	latest_review = get_latest_review_for_question(db, user_id=current_user.id, question_id=question.id)

	return QuestionWorkspaceResponse(
		question=detail,
		materials=detail.materials,
		answer_sections=detail.answer_sections,
		reference_answer=detail.reference_answer,
		optimized_example=detail.optimized_example,
		latest_draft=(
			QuestionWorkspaceDraft(
				session_id=current_session.id,
				answer_id=current_session.answer_id,
				status=current_session.status,
				answers=_json_loads(current_session.answers_json, {}),
				updated_at=current_session.updated_at,
			)
			if current_session is not None
			else None
		),
		latest_review=(
			QuestionWorkspaceLatestReview(
				review_id=latest_review.id,
				score=latest_review.score,
				created_at=latest_review.created_at,
			)
			if latest_review is not None
			else None
		),
	)


def get_question_filter_options(db: Session, current_user: User, *, user_id: int | None = None) -> QuestionFilterOptionsResponse:
	is_admin = _is_admin(db, current_user.id)
	if user_id is not None and not is_admin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可按用户筛选题库")
	# 普通用户：获取系统题库 + 自己题库的筛选项
	if is_admin:
		owner_id = user_id  # None = 全部
	else:
		owner_id = current_user.id
	question_types, tags, sources = list_question_filter_values(db, user_id=owner_id, include_system=not is_admin)
	return QuestionFilterOptionsResponse(question_types=question_types, tags=tags, sources=sources)


def create_question_bank_item(db: Session, current_user: User, data: QuestionCreate) -> QuestionRead:
	payload = _serialize_question_payload(data.model_dump())
	# 普通用户只能创建个人题目；管理员可指定 scope
	scope = payload.pop("scope", None) or "user"
	if scope == "system" and not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可创建系统题库题目")
	question = create_question(db, Question(user_id=current_user.id, scope=scope, **payload))
	db.commit()
	db.refresh(question)
	return _to_read_model(question)


def import_question_bank(db: Session, current_user: User, data: QuestionImportRequest) -> QuestionImportResult:
	imported: list[QuestionRead] = []
	failed: list[dict] = []
	# 导入时的 scope：管理员可指定 scope（默认 system），普通用户固定 user
	is_admin = _is_admin(db, current_user.id)
	default_scope = "system" if is_admin else "user"

	for index, item in enumerate(data.items):
		try:
			with db.begin_nested():
				payload = _serialize_question_payload(item.model_dump())
				scope = payload.pop("scope", None) or default_scope
				if scope == "system" and not is_admin:
					scope = "user"
				question = create_question(
					db,
					Question(
						user_id=current_user.id,
						scope=scope,
						**payload,
					),
				)
				imported.append(_to_read_model(question))
		except Exception as exc:
			failed.append({"index": index, "title": item.title, "message": str(exc)})
	db.commit()
	return QuestionImportResult(imported=imported, failed=failed)


def update_question_bank_item(db: Session, current_user: User, question_id: int, data: QuestionUpdate) -> QuestionRead:
	question = get_question(db, question_id)
	if question is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
	# 系统题库只有管理员可改；个人题库只有本人和管理员可改
	if question.scope == "system" and not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统题库仅管理员可修改")
	if question.scope != "system" and question.user_id != current_user.id and not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该题目")
	update_data = _serialize_question_payload(data.model_dump(exclude_unset=True))
	question = update_question(db, question, update_data)
	db.commit()
	db.refresh(question)
	return _to_read_model(question)


def delete_question_bank_item(db: Session, current_user: User, question_id: int) -> None:
	question = get_question(db, question_id)
	if question is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
	if question.scope == "system" and not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统题库仅管理员可删除")
	if question.scope != "system" and question.user_id != current_user.id and not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该题目")
	delete_question(db, question)
	db.commit()


def toggle_question_favorite(db: Session, current_user: User, question_id: int) -> dict:
	"""切换题目收藏状态。"""
	from app.modules.question.models import QuestionFavorite
	from sqlalchemy import select

	question = get_question(db, question_id)
	if question is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

	existing = db.scalars(
		select(QuestionFavorite).where(
			QuestionFavorite.user_id == current_user.id,
			QuestionFavorite.question_id == question_id,
		)
	).first()

	if existing is not None:
		db.delete(existing)
		db.commit()
		return {"question_id": question_id, "is_favorite": False}
	else:
		fav = QuestionFavorite(user_id=current_user.id, question_id=question_id)
		db.add(fav)
		db.commit()
		return {"question_id": question_id, "is_favorite": True}


def list_favorite_questions(
	db: Session,
	current_user: User,
	*,
	page: int = 1,
	page_size: int = 20,
) -> QuestionListResponse:
	"""获取用户收藏的题目列表。"""
	from app.modules.question.models import QuestionFavorite
	from sqlalchemy import func, select

	count_query = (
		select(func.count(QuestionFavorite.id))
		.where(QuestionFavorite.user_id == current_user.id)
	)
	total = db.scalar(count_query) or 0

	query = (
		select(Question)
		.join(QuestionFavorite, QuestionFavorite.question_id == Question.id)
		.where(QuestionFavorite.user_id == current_user.id)
		.order_by(QuestionFavorite.created_at.desc())
		.offset((page - 1) * page_size)
		.limit(page_size)
	)
	items = db.scalars(query).all()

	return QuestionListResponse(
		items=[_to_read_model(item) for item in items],
		total=total,
		page=page,
		page_size=page_size,
	)


__all__ = [
	"list_question_bank",
	"get_question_filter_options",
	"get_question_detail",
	"get_question_workspace",
	"create_question_bank_item",
	"import_question_bank",
	"update_question_bank_item",
	"delete_question_bank_item",
	"toggle_question_favorite",
	"list_favorite_questions",
]
