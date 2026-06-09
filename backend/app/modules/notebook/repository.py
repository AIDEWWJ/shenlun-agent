"""错题本与学习计划数据查询。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.notebook.models import ErrorNotebookEntry, StudyPlan
from app.modules.question.models import Question
from app.modules.review.models import Review


def list_error_notebook_entries(
    db: Session,
    user_id: int,
    *,
    status: str | None = None,
    question_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """分页查询错题本，join questions 和 reviews 获取题目信息。"""
    query = (
        select(
            ErrorNotebookEntry,
            Question.title.label("question_title"),
            Question.question_type.label("question_type"),
            Review.score.label("score"),
        )
        .join(Question, ErrorNotebookEntry.question_id == Question.id)
        .outerjoin(Review, ErrorNotebookEntry.review_id == Review.id)
        .where(ErrorNotebookEntry.user_id == user_id)
    )
    count_query = (
        select(func.count(ErrorNotebookEntry.id))
        .where(ErrorNotebookEntry.user_id == user_id)
    )

    if status:
        query = query.where(ErrorNotebookEntry.status == status)
        count_query = count_query.where(ErrorNotebookEntry.status == status)
    if question_type:
        query = query.where(Question.question_type == question_type)
        count_query = count_query.where(Question.question_type == question_type)

    total = db.scalar(count_query) or 0
    rows = db.execute(
        query.order_by(ErrorNotebookEntry.created_at.desc(), ErrorNotebookEntry.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = []
    for row in rows:
        entry = row[0]
        items.append({
            "entry": entry,
            "question_title": row[1],
            "question_type": row[2],
            "score": row[3],
        })
    return items, total


def get_error_notebook_entry(db: Session, entry_id: int) -> ErrorNotebookEntry | None:
    return db.get(ErrorNotebookEntry, entry_id)


def get_existing_error_entry(db: Session, user_id: int, review_id: int) -> ErrorNotebookEntry | None:
    """检查某次批改是否已在错题本中。"""
    return db.scalars(
        select(ErrorNotebookEntry).where(
            ErrorNotebookEntry.user_id == user_id,
            ErrorNotebookEntry.review_id == review_id,
        )
    ).first()


def get_low_score_reviews(
    db: Session,
    user_id: int,
    *,
    score_threshold: int = 60,
    limit: int = 20,
) -> list[Review]:
    """获取低分批改记录。"""
    return db.scalars(
        select(Review)
        .where(
            Review.user_id == user_id,
            Review.score.isnot(None),
            Review.score < score_threshold,
        )
        .order_by(Review.score.asc(), Review.created_at.desc())
        .limit(limit)
    ).all()


def create_error_notebook_entry(db: Session, entry: ErrorNotebookEntry) -> ErrorNotebookEntry:
    db.add(entry)
    db.flush()
    return entry


def update_error_notebook_entry(
    db: Session,
    entry: ErrorNotebookEntry,
    *,
    status: str | None = None,
    resolve_note: str | None = None,
    resolved_at: datetime | None = None,
) -> ErrorNotebookEntry:
    if status is not None:
        entry.status = status
    if resolve_note is not None:
        entry.resolve_note = resolve_note
    if resolved_at is not None:
        entry.resolved_at = resolved_at
    db.flush()
    return entry


# ========== 学习计划 ==========

def list_study_plans(
    db: Session,
    user_id: int,
    *,
    status: str | None = None,
) -> tuple[list[StudyPlan], int]:
    """查询用户学习计划。"""
    query = select(StudyPlan).where(StudyPlan.user_id == user_id)
    count_query = select(func.count(StudyPlan.id)).where(StudyPlan.user_id == user_id)

    if status:
        query = query.where(StudyPlan.status == status)
        count_query = count_query.where(StudyPlan.status == status)

    total = db.scalar(count_query) or 0
    items = db.scalars(
        query.order_by(StudyPlan.created_at.desc(), StudyPlan.id.desc())
    ).all()
    return items, total


def get_study_plan(db: Session, plan_id: int) -> StudyPlan | None:
    return db.get(StudyPlan, plan_id)


def create_study_plan(db: Session, plan: StudyPlan) -> StudyPlan:
    db.add(plan)
    db.flush()
    return plan


def get_questions_by_type(
    db: Session,
    user_id: int,
    question_type: str,
    *,
    limit: int = 3,
) -> list[Question]:
    """按题型获取题目。"""
    return db.scalars(
        select(Question)
        .where(Question.user_id == user_id, Question.question_type == question_type)
        .order_by(func.random())
        .limit(limit)
    ).all()


def get_all_question_types_for_user(db: Session, user_id: int) -> list[str]:
    """获取用户所有题型。"""
    rows = db.scalars(
        select(Question.question_type)
        .where(Question.user_id == user_id, Question.question_type.isnot(None), Question.question_type != "")
        .distinct()
    ).all()
    return [r for r in rows if r]
