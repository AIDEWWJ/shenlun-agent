from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.system_config.models import SystemConfig


def list_system_configs(db: Session) -> list[SystemConfig]:
    return db.scalars(select(SystemConfig).order_by(SystemConfig.category.asc(), SystemConfig.id.asc())).all()


def get_system_config(db: Session, config_key: str) -> SystemConfig | None:
    return db.scalars(select(SystemConfig).where(SystemConfig.config_key == config_key)).first()


def create_system_config(db: Session, config: SystemConfig) -> SystemConfig:
    db.add(config)
    db.flush()
    return config


def update_system_config(db: Session, config: SystemConfig, *, name: str | None = None, content_json: str | None = None) -> SystemConfig:
    if name is not None:
        config.name = name
    if content_json is not None:
        config.content_json = content_json
    db.flush()
    return config
