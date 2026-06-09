from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.library.service import get_library_filters, list_library_items
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(prefix="/library", tags=["用户-统一题库"])


@router.get("/items", response_model=ApiResponse, summary="分页查询统一题库条目")
def list_items(
    item_type: Literal["all", "paper", "question"] = Query(default="all"),
    scope: str | None = Query(default=None, description="题库范围：system / user，为空则全部可见"),
    keyword: str | None = Query(default=None),
    region: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    year: int | None = Query(default=None),
    question_type: str | None = Query(default=None),
    sort_by: Literal["created_at", "updated_at", "year", "title"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    page: int = Query(default=DEFAULT_PAGE, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = list_library_items(
        db,
        current_user,
        item_type=item_type,
        scope=scope,
        keyword=keyword,
        region=region,
        difficulty=difficulty,
        year=year,
        question_type=question_type,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, message="获取统一题库成功")


@router.get("/filters", response_model=ApiResponse, summary="获取统一题库筛选项")
def get_filters(
    scope: str | None = Query(default=None, description="题库范围：system / user，为空则全部可见"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return api_success(data=get_library_filters(db, current_user, scope=scope), message="获取统一题库筛选项成功")
