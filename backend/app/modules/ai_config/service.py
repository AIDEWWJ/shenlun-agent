"""AI 配置业务模块。"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.ai_config.models import AiConfig, Role, UserRole
from app.modules.ai_config.schemas import AiConfigListResponse


def is_admin(db: Session, user_id: int) -> bool:
	"""判断用户是否为管理员。"""

	return (
		db.scalars(
			select(Role.id)
			.join(UserRole, UserRole.role_id == Role.id)
			.where(UserRole.user_id == user_id, Role.name == "admin")
		).first()
		is not None
	)


def get_config_or_404(db: Session, config_id: int) -> AiConfig:
	"""根据 ID 获取 AI 配置，不存在时抛出 404。"""

	config = db.get(AiConfig, config_id)
	if config is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI 配置不存在")
	return config


def normalize_default(db: Session, config: AiConfig) -> None:
	"""保证同一作用域下只有一个默认配置。"""

	if not config.is_default:
		return

	query = select(AiConfig).where(AiConfig.id != config.id, AiConfig.scope == config.scope)
	if config.scope == "user" and config.user_id is not None:
		query = query.where(AiConfig.user_id == config.user_id)
	if config.scope == "system":
		query = query.where(AiConfig.user_id.is_(None))

	for item in db.scalars(query).all():
		item.is_default = False


def list_user_configs(db: Session, user_id: int) -> list[AiConfig]:
	"""查询个人配置列表。"""

	return db.scalars(
		select(AiConfig)
		.where(AiConfig.scope == "user", AiConfig.user_id == user_id)
		.order_by(AiConfig.is_default.desc(), AiConfig.created_at.desc())
	).all()


def list_user_configs_paginated(db: Session, user_id: int, *, page: int = 1, page_size: int = 20) -> AiConfigListResponse:
	query = select(AiConfig).where(AiConfig.scope == "user", AiConfig.user_id == user_id)
	count_query = select(func.count(AiConfig.id)).where(AiConfig.scope == "user", AiConfig.user_id == user_id)
	total = db.scalar(count_query) or 0
	items = db.scalars(
		query.order_by(AiConfig.is_default.desc(), AiConfig.created_at.desc())
		.offset((page - 1) * page_size)
		.limit(page_size)
	).all()
	return AiConfigListResponse(items=items, total=total, page=page, page_size=page_size)


def get_system_default_config(db: Session) -> AiConfig | None:
	"""获取系统默认配置。"""

	return db.scalars(
		select(AiConfig)
		.where(AiConfig.scope == "system", AiConfig.user_id.is_(None), AiConfig.is_default.is_(True))
		.order_by(AiConfig.created_at.desc())
	).first()


def list_system_configs(db: Session) -> list[AiConfig]:
	"""查询系统配置列表。"""

	return db.scalars(
		select(AiConfig)
		.where(AiConfig.scope == "system")
		.order_by(AiConfig.is_default.desc(), AiConfig.created_at.desc())
	).all()


def list_system_configs_paginated(db: Session, *, page: int = 1, page_size: int = 20) -> AiConfigListResponse:
	query = select(AiConfig).where(AiConfig.scope == "system")
	count_query = select(func.count(AiConfig.id)).where(AiConfig.scope == "system")
	total = db.scalar(count_query) or 0
	items = db.scalars(
		query.order_by(AiConfig.is_default.desc(), AiConfig.created_at.desc())
		.offset((page - 1) * page_size)
		.limit(page_size)
	).all()
	return AiConfigListResponse(items=items, total=total, page=page, page_size=page_size)


def get_effective_review_config(db: Session, user_id: int) -> AiConfig | None:
	"""获取用于答案批改的有效 AI 配置。"""

	user_configs = list_user_configs(db, user_id)
	for config in user_configs:
		if config.is_default:
			return config
	if user_configs:
		return user_configs[0]
	return get_system_default_config(db)


def create_ai_config(db: Session, config: AiConfig) -> AiConfig:
	"""创建 AI 配置并处理默认项。"""

	db.add(config)
	db.flush()
	normalize_default(db, config)
	db.commit()
	db.refresh(config)
	return config


def update_ai_config(db: Session, config: AiConfig, data: dict) -> AiConfig:
	"""更新 AI 配置并处理默认项。"""

	for field, value in data.items():
		setattr(config, field, value)

	normalize_default(db, config)
	db.commit()
	db.refresh(config)
	return config


def delete_ai_config(db: Session, config: AiConfig) -> None:
	"""删除 AI 配置。"""

	db.delete(config)
	db.commit()


__all__ = [
	"is_admin",
	"get_config_or_404",
	"normalize_default",
	"list_user_configs",
	"list_user_configs_paginated",
	"get_system_default_config",
	"list_system_configs",
	"list_system_configs_paginated",
	"get_effective_review_config",
	"create_ai_config",
	"update_ai_config",
	"delete_ai_config",
]
