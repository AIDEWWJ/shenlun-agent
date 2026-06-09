"""统一题库聚合服务。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.auth.repository import get_user_role_names
from app.modules.paper.models import Paper
from app.modules.practice.models import PaperPracticeSession
from app.modules.question.models import Question
from app.modules.library.schemas import (
    LibraryAction,
    LibraryFilterOptionsResponse,
    LibraryItemListResponse,
    LibraryItemRead,
    LibraryItemTypeFilter,
)


SortBy = Literal["created_at", "updated_at", "year", "title"]
SortOrder = Literal["asc", "desc"]


@dataclass(slots=True)
class _RawLibraryItem:
    read: LibraryItemRead
    sort_created_at: datetime | None
    sort_updated_at: datetime | None
    sort_year: int | None
    sort_title: str


def _is_admin(db: Session, user_id: int) -> bool:
    return "admin" in get_user_role_names(db, user_id)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _split_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _validate_scope(scope: str | None) -> None:
    if scope is not None and scope not in {"system", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的题库范围")


def _apply_visibility(query: Select, model, user: User, is_admin: bool, scope: str | None) -> Select:
    if scope == "system":
        return query.where(model.scope == "system")
    if scope == "user":
        return query.where(model.user_id == user.id, model.scope == "user")
    if is_admin:
        return query
    return query.where(or_(model.scope == "system", (model.user_id == user.id) & (model.scope == "user")))


def _paper_has_draft(session: PaperPracticeSession | None) -> bool:
    if session is None or session.status != "drafting":
        return False
    try:
        answers = json.loads(session.answers_json or "{}")
    except Exception:
        return False
    if not isinstance(answers, dict):
        return False
    return any(isinstance(value, str) and bool(value.strip()) for value in answers.values())


def _load_paper_draft_flags(db: Session, user_id: int, paper_ids: list[int]) -> dict[int, bool]:
    if not paper_ids:
        return {}
    sessions = db.scalars(
        select(PaperPracticeSession).where(
            PaperPracticeSession.user_id == user_id,
            PaperPracticeSession.paper_id.in_(paper_ids),
        )
    ).all()
    return {int(session.paper_id): _paper_has_draft(session) for session in sessions}


def _build_paper_query(
    user: User,
    is_admin: bool,
    *,
    scope: str | None,
    keyword: str | None,
    region: str | None,
    difficulty: str | None,
    year: int | None,
) -> Select:
    query = _apply_visibility(select(Paper), Paper, user, is_admin, scope)
    if keyword:
        like_keyword = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                Paper.title.ilike(like_keyword),
                Paper.category.ilike(like_keyword),
                Paper.region.ilike(like_keyword),
            )
        )
    if region:
        query = query.where(Paper.region == region)
    if difficulty:
        query = query.where(Paper.difficulty == difficulty)
    if year:
        query = query.where(Paper.year == year)
    return query


def _build_question_query(
    user: User,
    is_admin: bool,
    *,
    scope: str | None,
    keyword: str | None,
    region: str | None,
    difficulty: str | None,
    year: int | None,
    question_type: str | None,
) -> Select:
    query = _apply_visibility(select(Question), Question, user, is_admin, scope).where(Question.paper_id.is_(None))
    if keyword:
        like_keyword = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                Question.title.ilike(like_keyword),
                Question.content.ilike(like_keyword),
                Question.tags.ilike(like_keyword),
                Question.source.ilike(like_keyword),
                Question.question_type.ilike(like_keyword),
            )
        )
    if region:
        query = query.where(Question.region == region)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if year:
        query = query.where(Question.year == year)
    if question_type:
        query = query.where(Question.question_type == question_type)
    return query


def _to_paper_item(paper: Paper, has_draft: bool) -> _RawLibraryItem:
    primary_action = LibraryAction(
        label="继续练习" if has_draft else "开始练习",
        path=f"/practice/paper/{paper.id}{'?resume=1' if has_draft else ''}",
    )
    read = LibraryItemRead(
        item_key=f"paper:{paper.id}",
        item_type="paper",
        resource_id=int(paper.id),
        title=paper.title,
        source=paper.category,
        year=paper.year,
        region=paper.region,
        difficulty=paper.difficulty,
        question_type=None,
        question_count=paper.question_count,
        suggested_minutes=None,
        scope=paper.scope or "system",
        tags=[paper.category] if paper.category else [],
        has_draft=has_draft,
        created_at=_iso(paper.created_at),
        updated_at=_iso(paper.updated_at),
        primary_action=primary_action,
        secondary_action=LibraryAction(label="查看详情", path=f"/papers/{paper.id}"),
    )
    return _RawLibraryItem(
        read=read,
        sort_created_at=paper.created_at,
        sort_updated_at=paper.updated_at,
        sort_year=paper.year,
        sort_title=paper.title,
    )


def _to_question_item(question: Question) -> _RawLibraryItem:
    read = LibraryItemRead(
        item_key=f"question:{question.id}",
        item_type="question",
        resource_id=int(question.id),
        title=question.title,
        source=question.source or question.category,
        year=question.year,
        region=question.region,
        difficulty=question.difficulty,
        question_type=question.question_type,
        question_count=None,
        suggested_minutes=question.suggested_minutes,
        scope=question.scope or "user",
        tags=_split_tags(question.tags),
        has_draft=False,
        created_at=_iso(question.created_at),
        updated_at=_iso(question.created_at),
        primary_action=LibraryAction(label="开始练习", path=f"/practice/{question.id}"),
        secondary_action=None,
    )
    return _RawLibraryItem(
        read=read,
        sort_created_at=question.created_at,
        sort_updated_at=question.created_at,
        sort_year=question.year,
        sort_title=question.title,
    )


def _sort_items(items: list[_RawLibraryItem], sort_by: SortBy, sort_order: SortOrder) -> list[_RawLibraryItem]:
    reverse = sort_order == "desc"

    def key(item: _RawLibraryItem):
        if sort_by == "title":
            return (item.sort_title or "", item.read.item_type, item.read.resource_id)
        if sort_by == "year":
            year_value = item.sort_year if item.sort_year is not None else -1
            return (year_value, item.sort_created_at or datetime.min, item.read.resource_id)
        if sort_by == "updated_at":
            return (item.sort_updated_at or datetime.min, item.read.resource_id)
        return (item.sort_created_at or datetime.min, item.read.resource_id)

    return sorted(items, key=key, reverse=reverse)


def list_library_items(
    db: Session,
    user: User,
    *,
    item_type: LibraryItemTypeFilter = "all",
    scope: str | None = None,
    keyword: str | None = None,
    region: str | None = None,
    difficulty: str | None = None,
    year: int | None = None,
    question_type: str | None = None,
    sort_by: SortBy = "created_at",
    sort_order: SortOrder = "desc",
    page: int = 1,
    page_size: int = 20,
) -> LibraryItemListResponse:
    _validate_scope(scope)
    is_admin = _is_admin(db, user.id)
    raw_items: list[_RawLibraryItem] = []

    if item_type in {"all", "paper"} and not question_type:
        papers = db.scalars(
            _build_paper_query(
                user,
                is_admin,
                scope=scope,
                keyword=keyword,
                region=region,
                difficulty=difficulty,
                year=year,
            )
        ).all()
        draft_flags = _load_paper_draft_flags(db, user.id, [int(paper.id) for paper in papers])
        raw_items.extend(_to_paper_item(paper, draft_flags.get(int(paper.id), False)) for paper in papers)

    if item_type in {"all", "question"}:
        questions = db.scalars(
            _build_question_query(
                user,
                is_admin,
                scope=scope,
                keyword=keyword,
                region=region,
                difficulty=difficulty,
                year=year,
                question_type=question_type,
            )
        ).all()
        raw_items.extend(_to_question_item(question) for question in questions)

    sorted_items = _sort_items(raw_items, sort_by, sort_order)
    total = len(sorted_items)
    start = (page - 1) * page_size
    end = start + page_size

    return LibraryItemListResponse(
        items=[item.read for item in sorted_items[start:end]],
        total=total,
        page=page,
        page_size=page_size,
        applied_filters={
            "item_type": item_type,
            "scope": scope,
            "keyword": keyword,
            "region": region,
            "difficulty": difficulty,
            "year": year,
            "question_type": question_type,
        },
        applied_sort={"sort_by": sort_by, "sort_order": sort_order},
    )


def get_library_filters(db: Session, user: User, *, scope: str | None = None) -> LibraryFilterOptionsResponse:
    _validate_scope(scope)
    is_admin = _is_admin(db, user.id)
    papers = db.scalars(_build_paper_query(user, is_admin, scope=scope, keyword=None, region=None, difficulty=None, year=None)).all()
    questions = db.scalars(
        _build_question_query(
            user,
            is_admin,
            scope=scope,
            keyword=None,
            region=None,
            difficulty=None,
            year=None,
            question_type=None,
        )
    ).all()

    return LibraryFilterOptionsResponse(
        regions=sorted({value for value in [*(paper.region for paper in papers), *(question.region for question in questions)] if value}),
        years=sorted({value for value in [*(paper.year for paper in papers), *(question.year for question in questions)] if value}, reverse=True),
        difficulties=sorted({value for value in [*(paper.difficulty for paper in papers), *(question.difficulty for question in questions)] if value}),
        question_types=sorted({question.question_type for question in questions if question.question_type}),
    )
