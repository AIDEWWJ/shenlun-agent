from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint, func

from app.db.base import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"
    __table_args__ = (
        UniqueConstraint("config_key", name="uk_system_configs_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(64), nullable=False)
    config_key = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    content_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


__all__ = ["SystemConfig"]
