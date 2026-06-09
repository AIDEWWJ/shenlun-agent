from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.question.schemas import QuestionCreate, QuestionImportRequest, QuestionUpdate
from app.modules.question.service import (
	create_question_bank_item,
	delete_question_bank_item,
	get_question_detail,
	get_question_filter_options,
	get_question_workspace,
	import_question_bank,
	list_question_bank,
	toggle_question_favorite,
	list_favorite_questions,
	update_question_bank_item,
)
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(prefix="/questions", tags=["用户-题库"])


@router.get("", response_model=ApiResponse, summary="分页查询题库")
def list_questions(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	paper_id: int | None = Query(default=None, description="按试卷 ID 筛选小题"),
	keyword: str | None = Query(default=None),
	question_type: str | None = Query(default=None),
	tag: str | None = Query(default=None),
	source: str | None = Query(default=None),
	user_id: int | None = Query(default=None),
	scope: str | None = Query(default=None, description="题库范围：system / user，为空则全部可见"),
	sort_by: Literal["created_at", "title"] = Query(default="created_at"),
	sort_order: Literal["asc", "desc"] = Query(default="desc"),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	data = list_question_bank(
		db,
		current_user,
		page=page,
		page_size=page_size,
		paper_id=paper_id,
		keyword=keyword,
		question_type=question_type,
		tag=tag,
		source=source,
		user_id=user_id,
		scope=scope,
		sort_by=sort_by,
		sort_order=sort_order,
	)
	return api_success(data, message="获取题库列表成功")


@router.get("/filters", response_model=ApiResponse, summary="获取题库筛选项")
def get_question_filters(
	user_id: int | None = Query(default=None, ge=1),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	return api_success(
		get_question_filter_options(db, current_user, user_id=user_id),
		message="获取题库筛选项成功",
	)


@router.get("/favorites", response_model=ApiResponse, summary="获取收藏题目列表")
def get_favorites(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	return api_success(list_favorite_questions(db, current_user, page=page, page_size=page_size), message="获取收藏列表成功")


@router.get("/{question_id}/workspace", response_model=ApiResponse, summary="获取题目练习工作台")
def get_workspace(
	question_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	return api_success(get_question_workspace(db, current_user, question_id), message="获取题目工作台成功")


@router.get("/{question_id}", response_model=ApiResponse, summary="获取题目详情")
def get_question(
	question_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	return api_success(get_question_detail(db, current_user, question_id), message="获取题目详情成功")


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建题目")
def create_question(
	data: QuestionCreate,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	return api_success(create_question_bank_item(db, current_user, data), message="创建题目成功")


@router.post("/import", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="批量导入题目")
def import_questions(
	data: QuestionImportRequest,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	return api_success(import_question_bank(db, current_user, data), message="导入题库成功")


@router.put("/{question_id}", response_model=ApiResponse, summary="更新题目")
def update_question(
	question_id: int,
	data: QuestionUpdate,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	return api_success(update_question_bank_item(db, current_user, question_id, data), message="更新题目成功")


@router.delete("/{question_id}", response_model=ApiResponse, summary="删除题目")
def remove_question(
	question_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	delete_question_bank_item(db, current_user, question_id)
	return api_success(message="删除题目成功")


@router.patch("/{question_id}/favorite", response_model=ApiResponse, summary="切换题目收藏状态")
def toggle_favorite(
	question_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	result = toggle_question_favorite(db, current_user, question_id)
	message = "收藏成功" if result["is_favorite"] else "取消收藏成功"
	return api_success(result, message=message)
