from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.admin.service import create_admin_user, delete_admin_user, get_admin_user, list_admin_users, update_admin_user
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.deps import get_current_admin_user, get_db
from app.modules.admin.schemas import AdminUserCreate, AdminUserUpdate
from app.shared.schemas import ApiResponse


router = APIRouter(prefix="/admin/users", tags=["后台-用户管理"])


@router.get("", response_model=ApiResponse, summary="分页查询用户列表")
def list_users(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	"""管理员分页查询系统用户列表。"""
	return api_success(list_admin_users(db, page=page, page_size=page_size), message="获取用户列表成功")


@router.get("/{user_id}", response_model=ApiResponse, summary="获取用户详情")
def get_user(user_id: int, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员获取单个用户详情。"""
	return api_success(get_admin_user(db, user_id), message="获取用户详情成功")


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建用户")
def create_user(
	data: AdminUserCreate,
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	"""管理员创建用户账号和角色。"""
	return api_success(create_admin_user(db, data), message="创建用户成功")


@router.put("/{user_id}", response_model=ApiResponse, summary="更新用户")
def update_user(
	user_id: int,
	data: AdminUserUpdate,
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	"""管理员更新用户信息、角色、状态和密码。"""
	return api_success(update_admin_user(db, user_id, data), message="更新用户成功")


@router.delete("/{user_id}", response_model=ApiResponse, summary="删除用户")
def remove_user(user_id: int, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员删除指定用户。"""
	delete_admin_user(db, user_id)
	return api_success(message="删除用户成功")
