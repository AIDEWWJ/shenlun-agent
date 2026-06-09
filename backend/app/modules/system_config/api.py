from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.system_config.schemas import SystemConfigUpsertRequest
from app.modules.system_config.service import list_admin_system_configs, upsert_admin_system_config
from app.shared.deps import get_current_admin_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(prefix="/admin/system-configs", tags=["后台-系统运行配置"])


@router.get("", response_model=ApiResponse, summary="查询系统运行配置")
def list_system_runtime_configs(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """列出系统级阈值、词表、规则和回退配置。"""
    return api_success(list_admin_system_configs(db), message="获取系统运行配置成功")


@router.put("/{config_key}", response_model=ApiResponse, summary="更新系统运行配置")
def upsert_system_runtime_config(
    config_key: str,
    data: SystemConfigUpsertRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """更新指定类型的系统运行配置，未提供的字段会沿用默认值或旧值。"""
    return api_success(upsert_admin_system_config(db, config_key, data), message="更新系统运行配置成功")
