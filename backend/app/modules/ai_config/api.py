from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.ai_config.models import AiConfig
from app.modules.ai_config.schemas import (
	AiConfigAdminCreate,
	AiConfigAdminUpdate,
	AiConfigCreate,
	AiConfigUpdate,
)
from app.modules.ai_config.service import (
	create_ai_config,
	delete_ai_config,
	get_config_or_404,
	get_system_default_config,
	list_system_configs_paginated,
	list_user_configs_paginated,
	normalize_default,
	update_ai_config,
)
from app.modules.auth.models import User
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.shared.deps import get_current_active_user, get_current_admin_user, get_db
from app.shared.schemas import ApiResponse


user_router = APIRouter(tags=["用户-AI 配置"])
admin_router = APIRouter(prefix="/admin/ai-configs/system", tags=["后台-系统 AI 配置"])


@user_router.get("/ai-configs/me", response_model=ApiResponse, summary="查询个人模型配置")
def list_my_configs(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	configs = list_user_configs_paginated(db, current_user.id, page=page, page_size=page_size)
	return api_success(configs, message="获取个人 AI 配置成功")


@user_router.get("/ai-configs/system-default", response_model=ApiResponse, summary="获取系统默认模型配置")
def get_system_default(db: Session = Depends(get_db)):
	config = get_system_default_config(db)
	return api_success(config, message="获取系统默认 AI 配置成功")


@user_router.post("/ai-configs/me", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建个人模型配置")
def create_my_config(
	data: AiConfigCreate,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	config = create_ai_config(
		db,
		AiConfig(
			user_id=current_user.id,
			scope="user",
			created_by=current_user.id,
			provider=data.provider,
			model_name=data.model_name,
			api_key=data.api_key,
			base_url=data.base_url,
			temperature=data.temperature,
			is_default=data.is_default,
		),
	)
	return api_success(config, message="创建个人 AI 配置成功")


@user_router.put("/ai-configs/me/{config_id}", response_model=ApiResponse, summary="更新个人模型配置")
def update_my_config(
	config_id: int,
	data: AiConfigUpdate,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	config = get_config_or_404(db, config_id)
	if config.scope != "user" or config.user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该配置")

	config = update_ai_config(db, config, data.model_dump(exclude_unset=True))
	return api_success(config, message="更新个人 AI 配置成功")


@user_router.delete("/ai-configs/me/{config_id}", response_model=ApiResponse, summary="删除个人模型配置")
def delete_my_config(
	config_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	config = get_config_or_404(db, config_id)
	if config.scope != "user" or config.user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该配置")
	delete_ai_config(db, config)
	return api_success(message="删除个人 AI 配置成功")


@user_router.post("/ai-configs/me/{config_id}/default", response_model=ApiResponse, summary="设为个人默认模型配置")
def set_my_default_config(
	config_id: int,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	config = get_config_or_404(db, config_id)
	if config.scope != "user" or config.user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权设置该配置")

	config.is_default = True
	normalize_default(db, config)
	db.commit()
	db.refresh(config)
	return api_success(config, message="已设为默认配置")


@admin_router.get("", response_model=ApiResponse, summary="分页查询系统模型配置")
def list_system_configs(
	page: int = Query(default=DEFAULT_PAGE, ge=1),
	page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	configs = list_system_configs_paginated(db, page=page, page_size=page_size)
	return api_success(configs, message="获取系统 AI 配置成功")


@admin_router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建系统模型配置")
def create_system_config(
	data: AiConfigAdminCreate,
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	config = create_ai_config(
		db,
		AiConfig(
			user_id=None,
			scope="system",
			created_by=current_user.id,
			provider=data.provider,
			model_name=data.model_name,
			api_key=data.api_key,
			base_url=data.base_url,
			temperature=data.temperature,
			is_default=data.is_default,
		),
	)
	return api_success(config, message="创建系统 AI 配置成功")


@admin_router.put("/{config_id}", response_model=ApiResponse, summary="更新系统模型配置")
def update_system_config(
	config_id: int,
	data: AiConfigAdminUpdate,
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	config = get_config_or_404(db, config_id)
	if config.scope != "system":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")

	update_data = data.model_dump(exclude_unset=True)
	update_data["scope"] = "system"
	update_data["user_id"] = None
	config = update_ai_config(db, config, update_data)
	return api_success(config, message="更新系统 AI 配置成功")


@admin_router.delete("/{config_id}", response_model=ApiResponse, summary="删除系统模型配置")
def delete_system_config(
	config_id: int,
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	config = get_config_or_404(db, config_id)
	if config.scope != "system":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")
	delete_ai_config(db, config)
	return api_success(message="删除系统 AI 配置成功")


@admin_router.post("/{config_id}/default", response_model=ApiResponse, summary="设为系统默认模型配置")
def set_system_default_config(
	config_id: int,
	current_user: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	config = get_config_or_404(db, config_id)
	if config.scope != "system":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")

	config.is_default = True
	normalize_default(db, config)
	db.commit()
	db.refresh(config)
	return api_success(config, message="已设为系统默认配置")
