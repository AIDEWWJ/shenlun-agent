from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.response import api_success
from app.models import AiConfig, User
from app.schemas.common import ApiResponse
from app.schemas.ai_config import (
    AiConfigAdminCreate,
    AiConfigAdminUpdate,
    AiConfigCreate,
    AiConfigRead,
    AiConfigUpdate,
)
from app.services.ai_config_service import (
    create_ai_config,
    delete_ai_config,
    get_config_or_404,
    get_system_default_config,
    is_admin,
    list_system_configs as list_system_configs_service,
    list_user_configs,
    normalize_default,
    update_ai_config,
)


router = APIRouter(tags=["ai-configs"])


@router.get("/ai-configs/me", response_model=ApiResponse)
def list_my_configs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    configs = list_user_configs(db, current_user.id)
    return api_success(configs, message="获取个人 AI 配置成功")


@router.get("/ai-configs/system-default", response_model=ApiResponse)
def get_system_default(db: Session = Depends(get_db)):
    config = get_system_default_config(db)
    return api_success(config, message="获取系统默认 AI 配置成功")


@router.post("/ai-configs/me", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
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
            system_prompt=data.system_prompt,
            is_default=data.is_default,
        ),
    )
    return api_success(config, message="创建个人 AI 配置成功")


@router.put("/ai-configs/me/{config_id}", response_model=ApiResponse)
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


@router.delete("/ai-configs/me/{config_id}", response_model=ApiResponse)
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


@router.post("/ai-configs/me/{config_id}/default", response_model=ApiResponse)
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


@router.get("/admin/ai-configs/system", response_model=ApiResponse)
def list_system_configs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    configs = list_system_configs_service(db)
    return api_success(configs, message="获取系统 AI 配置成功")


@router.post("/admin/ai-configs/system", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_system_config(
    data: AiConfigAdminCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

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
            system_prompt=data.system_prompt,
            is_default=data.is_default,
        ),
    )
    return api_success(config, message="创建系统 AI 配置成功")


@router.put("/admin/ai-configs/system/{config_id}", response_model=ApiResponse)
def update_system_config(
    config_id: int,
    data: AiConfigAdminUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    config = get_config_or_404(db, config_id)
    if config.scope != "system":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")

    update_data = data.model_dump(exclude_unset=True)
    update_data["scope"] = "system"
    update_data["user_id"] = None
    config = update_ai_config(db, config, update_data)
    return api_success(config, message="更新系统 AI 配置成功")


@router.delete("/admin/ai-configs/system/{config_id}", response_model=ApiResponse)
def delete_system_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    config = get_config_or_404(db, config_id)
    if config.scope != "system":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")
    delete_ai_config(db, config)
    return api_success(message="删除系统 AI 配置成功")


@router.post("/admin/ai-configs/system/{config_id}/default", response_model=ApiResponse)
def set_system_default_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    config = get_config_or_404(db, config_id)
    if config.scope != "system":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")

    config.is_default = True
    normalize_default(db, config)
    db.commit()
    db.refresh(config)
    return api_success(config, message="已设为系统默认配置")
