from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.modules.email.service import (
	create_email_config_item,
	create_email_template_item,
	delete_email_config_item,
	delete_email_template_item,
	list_email_config_read_models,
	list_email_template_read_models,
	update_email_config_item,
	update_email_template_item,
)
from app.shared.deps import get_current_admin_user, get_db
from app.shared.schemas import ApiResponse
from app.modules.email.schemas import EmailConfigCreate, EmailConfigUpdate, EmailTemplateCreate, EmailTemplateUpdate


router = APIRouter(prefix="/admin/email", tags=["后台-邮件管理"])


@router.get("/configs", response_model=ApiResponse, summary="分页查询邮件发送配置")
def list_configs(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	"""管理员分页查询 SMTP 发送配置。"""
	return api_success(list_email_config_read_models(db, page=page, page_size=page_size), message="获取邮件配置成功")


@router.post("/configs", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建邮件发送配置")
def create_config(data: EmailConfigCreate, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员创建新的 SMTP 发送配置。"""
	return api_success(create_email_config_item(db, data), message="创建邮件配置成功")


@router.put("/configs/{config_id}", response_model=ApiResponse, summary="更新邮件发送配置")
def update_config(config_id: int, data: EmailConfigUpdate, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员更新指定邮件发送配置。"""
	return api_success(update_email_config_item(db, config_id, data), message="更新邮件配置成功")


@router.delete("/configs/{config_id}", response_model=ApiResponse, summary="删除邮件发送配置")
def delete_config(config_id: int, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员删除指定邮件发送配置。"""
	delete_email_config_item(db, config_id)
	return api_success(message="删除邮件配置成功")


@router.get("/templates", response_model=ApiResponse, summary="分页查询邮件模板")
def list_templates(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	"""管理员分页查询邮件模板。"""
	return api_success(list_email_template_read_models(db, page=page, page_size=page_size), message="获取邮件模板成功")


@router.post("/templates", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建邮件模板")
def create_template(data: EmailTemplateCreate, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员创建邮件模板。"""
	return api_success(create_email_template_item(db, data), message="创建邮件模板成功")


@router.put("/templates/{template_key}", response_model=ApiResponse, summary="更新邮件模板")
def update_template(template_key: str, data: EmailTemplateUpdate, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员更新指定邮件模板。"""
	return api_success(update_email_template_item(db, template_key, data), message="更新邮件模板成功")


@router.delete("/templates/{template_key}", response_model=ApiResponse, summary="删除邮件模板")
def delete_template(template_key: str, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
	"""管理员删除指定邮件模板。"""
	delete_email_template_item(db, template_key)
	return api_success(message="删除邮件模板成功")
