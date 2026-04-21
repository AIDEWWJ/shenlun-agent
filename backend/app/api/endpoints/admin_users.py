from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.response import api_success
from app.models import Role, User, UserRole
from app.schemas.admin_user import AdminUserCreate, AdminUserUpdate
from app.schemas.common import ApiResponse
from app.services.user_service import (
    create_admin_user,
    delete_admin_user,
    get_admin_user,
    list_admin_users,
    update_admin_user,
)


router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _is_admin(db: Session, user_id: int) -> bool:
    """判断用户是否为管理员。"""

    return (
        db.scalars(
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.name == "admin")
        ).first()
        is not None
    )


@router.get("", response_model=ApiResponse)
def list_users(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    return api_success(list_admin_users(db), message="获取用户列表成功")


@router.get("/{user_id}", response_model=ApiResponse)
def get_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    return api_success(get_admin_user(db, user_id), message="获取用户详情成功")


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: AdminUserCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    return api_success(create_admin_user(db, data), message="创建用户成功")


@router.put("/{user_id}", response_model=ApiResponse)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    return api_success(update_admin_user(db, user_id, data), message="更新用户成功")


@router.delete("/{user_id}", response_model=ApiResponse)
def remove_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    delete_admin_user(db, user_id)
    return api_success(message="删除用户成功")
