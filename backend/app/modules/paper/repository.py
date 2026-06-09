from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.paper.models import Paper


def list_papers(
    db: Session,
    *,
    user_id: int | None = None,
    scope: str | None = None,
    include_system: bool = False,
    keyword: str | None = None,
    region: str | None = None,
    difficulty: str | None = None,
    year: int | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Paper], int]:
    query = select(Paper)
    count_query = select(func.count(Paper.id))

    if include_system and user_id is not None:
        if scope == "system":
            visibility = Paper.scope == "system"
        elif scope == "user":
            visibility = (Paper.user_id == user_id) & (Paper.scope == "user")
        else:
            visibility = (Paper.scope == "system") | ((Paper.user_id == user_id) & (Paper.scope == "user"))
        query = query.where(visibility)
        count_query = count_query.where(visibility)
    else:
        if user_id is not None:
            query = query.where(Paper.user_id == user_id)
            count_query = count_query.where(Paper.user_id == user_id)
        if scope is not None:
            query = query.where(Paper.scope == scope)
            count_query = count_query.where(Paper.scope == scope)

    conditions = []
    if keyword:
        like_keyword = f"%{keyword.strip()}%"
        conditions.append(Paper.title.ilike(like_keyword) | Paper.region.ilike(like_keyword))
    if region:
        conditions.append(Paper.region == region)
    if difficulty:
        conditions.append(Paper.difficulty == difficulty)
    if year:
        conditions.append(Paper.year == year)

    for condition in conditions:
        query = query.where(condition)
        count_query = count_query.where(condition)

    order_column = Paper.created_at if sort_by == "created_at" else Paper.title
    if sort_order == "asc":
        query = query.order_by(order_column.asc(), Paper.id.asc())
    else:
        query = query.order_by(order_column.desc(), Paper.id.desc())

    total = db.scalar(count_query) or 0
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def get_paper(db: Session, paper_id: int) -> Paper | None:
    return db.get(Paper, paper_id)


def create_paper(db: Session, paper: Paper) -> Paper:
    db.add(paper)
    db.flush()
    return paper


def update_paper(db: Session, paper: Paper, update_data: dict) -> Paper:
    for key, value in update_data.items():
        setattr(paper, key, value)
    db.flush()
    return paper


def delete_paper(db: Session, paper: Paper) -> None:
    db.delete(paper)
    db.flush()
