from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.response import api_success
from app.models import Role, User, UserRole
from app.schemas.common import ApiResponse
from app.schemas.email import (
	EmailConfigCreate,
	EmailConfigUpdate,
	EmailTemplateCreate,
	EmailTemplateUpdate,
)
from app.services.email_service import (
	create_email_config_item,
	create_email_template_item,
	delete_email_config_item,
	delete_email_template_item,
	list_email_config_read_models,
	list_email_template_read_models,
	update_email_config_item,
	update_email_template_item,
)


router = APIRouter(prefix="/admin/email", tags=["admin-email"])


def _is_admin(db: Session, user_id: int) -> bool:
	return (
		db.scalars(
			select(Role.id)
			.join(UserRole, UserRole.role_id == Role.id)
			.where(UserRole.user_id == user_id, Role.name == "admin")
		).first()
		is not None
	)


@router.get("/configs", response_model=ApiResponse)
def list_configs(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	return api_success(list_email_config_read_models(db), message="获取邮件配置成功")


@router.post("/configs", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_config(data: EmailConfigCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	return api_success(create_email_config_item(db, data), message="创建邮件配置成功")


@router.put("/configs/{config_id}", response_model=ApiResponse)
def update_config(config_id: int, data: EmailConfigUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	return api_success(update_email_config_item(db, config_id, data), message="更新邮件配置成功")


@router.delete("/configs/{config_id}", response_model=ApiResponse)
def delete_config(config_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	delete_email_config_item(db, config_id)
	return api_success(message="删除邮件配置成功")


@router.get("/templates", response_model=ApiResponse)
def list_templates(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	return api_success(list_email_template_read_models(db), message="获取邮件模板成功")


@router.post("/templates", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_template(data: EmailTemplateCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	return api_success(create_email_template_item(db, data), message="创建邮件模板成功")


@router.put("/templates/{template_key}", response_model=ApiResponse)
def update_template(template_key: str, data: EmailTemplateUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	return api_success(update_email_template_item(db, template_key, data), message="更新邮件模板成功")


@router.delete("/templates/{template_key}", response_model=ApiResponse)
def delete_template(template_key: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	if not _is_admin(db, current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
	delete_email_template_item(db, template_key)
	return api_success(message="删除邮件模板成功")
