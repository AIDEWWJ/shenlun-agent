from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.question.models import Question


def list_questions(
	db: Session,
	*,
	user_id: int | None = None,
	scope: str | None = None,
	include_system: bool = False,
	paper_id: int | None = None,
	keyword: str | None = None,
	question_type: str | None = None,
	tag: str | None = None,
	source: str | None = None,
	sort_by: str = "created_at",
	sort_order: str = "desc",
	page: int = 1,
	page_size: int = 20,
) -> tuple[list[Question], int]:
	"""分页查询题目列表。

	include_system=True 时，查询结果包含 scope='system' 的全部题目 + user_id 的个人题目。
	"""

	query = select(Question)
	count_query = select(func.count(Question.id))

	# 构建可见范围条件
	if include_system and user_id is not None:
		# 普通用户：看系统题库 + 自己的个人题库
		if scope == "system":
			visibility = Question.scope == "system"
		elif scope == "user":
			visibility = (Question.user_id == user_id) & (Question.scope == "user")
		else:
			visibility = (Question.scope == "system") | ((Question.user_id == user_id) & (Question.scope == "user"))
		query = query.where(visibility)
		count_query = count_query.where(visibility)
	else:
		# 管理员或无特殊要求
		if user_id is not None:
			query = query.where(Question.user_id == user_id)
			count_query = count_query.where(Question.user_id == user_id)
		if scope is not None:
			query = query.where(Question.scope == scope)
			count_query = count_query.where(Question.scope == scope)

	# 按试卷筛选
	if paper_id is not None:
		query = query.where(Question.paper_id == paper_id)
		count_query = count_query.where(Question.paper_id == paper_id)

	conditions = []
	if keyword:
		like_keyword = f"%{keyword.strip()}%"
		conditions.append(
			(Question.title.ilike(like_keyword))
			| (Question.content.ilike(like_keyword))
			| (Question.tags.ilike(like_keyword))
			| (Question.source.ilike(like_keyword))
			| (Question.question_type.ilike(like_keyword))
		)
	if question_type:
		conditions.append(Question.question_type == question_type)
	if tag:
		like_tag = f"%{tag.strip()}%"
		conditions.append(Question.tags.ilike(like_tag))
	if source:
		conditions.append(Question.source == source)

	if conditions:
		for condition in conditions:
			query = query.where(condition)
			count_query = count_query.where(condition)

	order_column = Question.created_at if sort_by == "created_at" else Question.title
	if sort_order == "asc":
		query = query.order_by(order_column.asc(), Question.id.asc())
	else:
		query = query.order_by(order_column.desc(), Question.id.desc())

	total = db.scalar(count_query) or 0
	items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
	return items, total


def get_question(db: Session, question_id: int) -> Question | None:
	"""根据 ID 获取题目。"""

	return db.get(Question, question_id)


def list_question_filter_values(db: Session, *, user_id: int | None = None, include_system: bool = False) -> tuple[list[str], list[str], list[str]]:
	base_query = select(Question.question_type, Question.tags, Question.source)

	if include_system and user_id is not None:
		base_query = base_query.where(
			(Question.scope == "system") | ((Question.user_id == user_id) & (Question.scope == "user"))
		)
	elif user_id is not None:
		base_query = base_query.where(Question.user_id == user_id)

	rows = db.execute(base_query).all()
	question_types = sorted({row[0].strip() for row in rows if row[0] and row[0].strip()})
	sources = sorted({row[2].strip() for row in rows if row[2] and row[2].strip()})
	tags: set[str] = set()
	for _, tag_value, _ in rows:
		if not tag_value:
			continue
		for item in tag_value.split(","):
			cleaned = item.strip()
			if cleaned:
				tags.add(cleaned)
	return question_types, sorted(tags), sources


def create_question(db: Session, question: Question) -> Question:
	"""创建题目。"""

	db.add(question)
	db.flush()
	return question


def update_question(db: Session, question: Question, update_data: dict) -> Question:
	"""更新题目。"""

	for key, value in update_data.items():
		setattr(question, key, value)
	db.flush()
	return question


def delete_question(db: Session, question: Question) -> None:
	"""删除题目。"""

	db.delete(question)
	db.flush()
