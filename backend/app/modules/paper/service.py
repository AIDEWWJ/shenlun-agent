"""试卷业务模块。"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.auth.repository import get_user_role_names
from app.modules.paper.models import Paper, PaperMaterial
from app.modules.paper import repository as paper_repo
from app.modules.question.models import Question
from app.modules.question import repository as question_repo


def _is_admin(db: Session, user_id: int) -> bool:
    return "admin" in get_user_role_names(db, user_id)


def _to_read_dict(paper: Paper) -> dict:
    return {
        "id": paper.id,
        "title": paper.title,
        "category": paper.category,
        "region": paper.region,
        "difficulty": paper.difficulty,
        "year": paper.year,
        "source_url": paper.source_url,
        "scope": paper.scope,
        "question_count": paper.question_count,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
    }


def list_paper_bank(
    db: Session,
    user: User,
    *,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    region: str | None = None,
    difficulty: str | None = None,
    year: int | None = None,
    scope: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    is_adm = _is_admin(db, user.id)

    if is_adm:
        items, total = paper_repo.list_papers(
            db, user_id=user.id, scope=scope, include_system=False,
            keyword=keyword, region=region, difficulty=difficulty, year=year,
            sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size,
        )
    else:
        items, total = paper_repo.list_papers(
            db, user_id=user.id, scope=scope, include_system=True,
            keyword=keyword, region=region, difficulty=difficulty, year=year,
            sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size,
        )

    return {
        "items": [_to_read_dict(p) for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_paper_filter_options(db: Session, user: User, scope: str | None = None) -> dict:
    """获取筛选项（地区、年份、难度）。"""
    is_adm = _is_admin(db, user.id)

    if is_adm:
        items, _ = paper_repo.list_papers(
            db, user_id=user.id, scope=scope, include_system=False, page_size=1000,
        )
    else:
        items, _ = paper_repo.list_papers(
            db, user_id=user.id, scope=scope, include_system=True, page_size=1000,
        )

    regions = sorted({p.region for p in items if p.region})
    years = sorted({p.year for p in items if p.year}, reverse=True)
    difficulties = sorted({p.difficulty for p in items if p.difficulty})

    return {
        "regions": regions,
        "years": years,
        "difficulties": difficulties,
    }


def get_paper_detail(db: Session, paper_id: int, user: User) -> dict:
    paper = paper_repo.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试卷不存在")

    materials_data = []
    for m in sorted(paper.materials, key=lambda x: x.material_num or 0):
        materials_data.append({
            "id": m.id,
            "material_num": m.material_num,
            "content": m.content,
            "sort_order": m.sort_order,
        })

    questions_data = []
    for q in sorted(paper.questions, key=lambda x: x.sort_order or 0):
        questions_data.append({
            "id": q.id,
            "material_refs": q.material_refs,
            "requirement": q.requirement,
            "reference_answer": q.reference_answer,
            "difficulty": q.difficulty,
            "sort_order": q.sort_order,
            "question_type": q.question_type,
        })

    data = _to_read_dict(paper)
    data["materials"] = materials_data
    data["questions"] = questions_data
    return data


def create_paper_item(db: Session, user: User, body: dict) -> dict:
    title = body.get("title")
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="试卷标题不能为空")

    paper = Paper(
        user_id=user.id,
        scope=body.get("scope", "system"),
        title=title,
        category=body.get("category"),
        region=body.get("region"),
        difficulty=body.get("difficulty"),
        year=body.get("year"),
        source_url=body.get("source_url"),
    )
    paper = paper_repo.create_paper(db, paper)
    db.commit()
    return _to_read_dict(paper)


def import_paper_with_questions(db: Session, user: User, body: dict) -> dict:
    """导入试卷+材料+小题。"""
    title = body.get("title")
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="试卷标题不能为空")

    paper = Paper(
        user_id=user.id,
        scope=body.get("scope", "system"),
        title=title,
        category=body.get("category"),
        region=body.get("region"),
        difficulty=body.get("difficulty"),
        year=body.get("year"),
        source_url=body.get("source_url"),
    )
    paper = paper_repo.create_paper(db, paper)

    # 导入材料
    materials_data = body.get("materials", [])
    for m_data in materials_data:
        material = PaperMaterial(
            paper_id=paper.id,
            material_num=m_data.get("material_num", 0),
            content=m_data.get("content", ""),
            sort_order=m_data.get("sort_order"),
        )
        db.add(material)

    # 导入小题
    questions_data = body.get("questions", [])
    created_count = 0
    for idx, q_data in enumerate(questions_data, start=1):
        material_refs = q_data.get("material_refs")
        requirement = q_data.get("requirement", "")
        content = requirement or ""

        question = Question(
            user_id=user.id,
            paper_id=paper.id,
            scope=paper.scope,
            title=f"{title} - 第{idx}题",
            content=content,
            material_refs=material_refs,
            requirement=requirement or None,
            sort_order=q_data.get("sort_order", idx),
            category=paper.category,
            year=paper.year,
            region=paper.region,
            question_type=q_data.get("question_type"),
            difficulty=q_data.get("difficulty", paper.difficulty),
            reference_answer=q_data.get("answer"),
        )
        question_repo.create_question(db, question)
        created_count += 1

    paper.question_count = created_count
    db.commit()

    return {
        "paper": _to_read_dict(paper),
        "materials_created": len(materials_data),
        "questions_created": created_count,
    }


def delete_paper_item(db: Session, paper_id: int, user: User) -> None:
    paper = paper_repo.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试卷不存在")
    paper_repo.delete_paper(db, paper)
    db.commit()
