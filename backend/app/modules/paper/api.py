from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.paper.service import (
    create_paper_item,
    delete_paper_item,
    get_paper_detail,
    import_paper_with_questions,
    list_paper_bank,
)
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse

router = APIRouter(prefix="/papers", tags=["试卷"])


@router.get("", response_model=ApiResponse, summary="分页查询试卷列表")
def list_papers(
    keyword: str | None = Query(default=None),
    region: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    year: int | None = Query(default=None),
    scope: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=DEFAULT_PAGE, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = list_paper_bank(
        db, current_user,
        page=page, page_size=page_size,
        keyword=keyword, region=region, difficulty=difficulty, year=year,
        scope=scope, sort_by=sort_by, sort_order=sort_order,
    )
    return api_success(data=data)


@router.get("/filters", response_model=ApiResponse, summary="获取筛选项")
def get_filters(
    scope: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.modules.paper.service import get_paper_filter_options
    data = get_paper_filter_options(db, current_user, scope=scope)
    return api_success(data=data)


@router.get("/{paper_id}", response_model=ApiResponse, summary="试卷详情（含小题列表）")
def get_paper(
    paper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = get_paper_detail(db, paper_id, current_user)
    return api_success(data=data)


@router.post("", response_model=ApiResponse, status_code=201, summary="创建试卷")
def create_paper(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = create_paper_item(db, current_user, body)
    return api_success(data=data)


@router.post("/import", response_model=ApiResponse, status_code=201, summary="批量导入试卷+小题")
def import_paper(
    body: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = import_paper_with_questions(db, current_user, body)
    return api_success(data=data)


@router.delete("/{paper_id}", response_model=ApiResponse, summary="删除试卷")
def delete_paper(
    paper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    delete_paper_item(db, paper_id, current_user)
    return api_success(message="试卷已删除")
