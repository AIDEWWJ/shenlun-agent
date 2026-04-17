from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models import AiConfig, Role, User, UserRole
from app.schemas.ai_config import (
    AiConfigAdminCreate,
    AiConfigAdminUpdate,
    AiConfigCreate,
    AiConfigRead,
    AiConfigUpdate,
)


router = APIRouter(tags=["ai-configs"])


def _is_admin(db: Session, user_id: int) -> bool:
    return (
        db.scalars(
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.name == "admin")
        ).first()
        is not None
    )


def _get_config_or_404(db: Session, config_id: int) -> AiConfig:
    config = db.get(AiConfig, config_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI 配置不存在")
    return config


def _normalize_default(db: Session, config: AiConfig) -> None:
    if not config.is_default:
        return

    query = select(AiConfig).where(AiConfig.id != config.id, AiConfig.scope == config.scope)
    if config.scope == "user" and config.user_id is not None:
        query = query.where(AiConfig.user_id == config.user_id)
    if config.scope == "system":
        query = query.where(AiConfig.user_id.is_(None))

    for item in db.scalars(query).all():
        item.is_default = False


@router.get("/ai-configs/me", response_model=list[AiConfigRead])
def list_my_configs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    configs = db.scalars(
        select(AiConfig)
        .where(AiConfig.scope == "user", AiConfig.user_id == current_user.id)
        .order_by(AiConfig.is_default.desc(), AiConfig.created_at.desc())
    ).all()
    return configs


@router.get("/ai-configs/system-default", response_model=AiConfigRead | None)
def get_system_default(db: Session = Depends(get_db)):
    return db.scalars(
        select(AiConfig)
        .where(AiConfig.scope == "system", AiConfig.user_id.is_(None), AiConfig.is_default.is_(True))
        .order_by(AiConfig.created_at.desc())
    ).first()


@router.post("/ai-configs/me", response_model=AiConfigRead, status_code=status.HTTP_201_CREATED)
def create_my_config(
    data: AiConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    config = AiConfig(
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
    )
    db.add(config)
    db.flush()
    _normalize_default(db, config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/ai-configs/me/{config_id}", response_model=AiConfigRead)
def update_my_config(
    config_id: int,
    data: AiConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    config = _get_config_or_404(db, config_id)
    if config.scope != "user" or config.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该配置")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    _normalize_default(db, config)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/ai-configs/me/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    config = _get_config_or_404(db, config_id)
    if config.scope != "user" or config.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该配置")
    db.delete(config)
    db.commit()


@router.post("/ai-configs/me/{config_id}/default", response_model=AiConfigRead)
def set_my_default_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    config = _get_config_or_404(db, config_id)
    if config.scope != "user" or config.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权设置该配置")

    config.is_default = True
    _normalize_default(db, config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/admin/ai-configs/system", response_model=list[AiConfigRead])
def list_system_configs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    return db.scalars(
        select(AiConfig)
        .where(AiConfig.scope == "system")
        .order_by(AiConfig.is_default.desc(), AiConfig.created_at.desc())
    ).all()


@router.post("/admin/ai-configs/system", response_model=AiConfigRead, status_code=status.HTTP_201_CREATED)
def create_system_config(
    data: AiConfigAdminCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    config = AiConfig(
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
    )
    db.add(config)
    db.flush()
    _normalize_default(db, config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/admin/ai-configs/system/{config_id}", response_model=AiConfigRead)
def update_system_config(
    config_id: int,
    data: AiConfigAdminUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    config = _get_config_or_404(db, config_id)
    if config.scope != "system":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    config.scope = "system"
    config.user_id = None
    _normalize_default(db, config)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/admin/ai-configs/system/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    config = _get_config_or_404(db, config_id)
    if config.scope != "system":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")
    db.delete(config)
    db.commit()


@router.post("/admin/ai-configs/system/{config_id}/default", response_model=AiConfigRead)
def set_system_default_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not _is_admin(db, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")

    config = _get_config_or_404(db, config_id)
    if config.scope != "system":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不是系统默认配置")

    config.is_default = True
    _normalize_default(db, config)
    db.commit()
    db.refresh(config)
    return config
