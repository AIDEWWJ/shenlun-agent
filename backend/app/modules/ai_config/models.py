from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.modules.auth.models import Role, UserRole


class AiConfig(Base):
	__tablename__ = "ai_configs"
	__table_args__ = (
		Index("idx_ai_configs_scope_user_default_created", "scope", "user_id", "is_default", "created_at"),
		Index("idx_ai_configs_created_by", "created_by"),
		Index("idx_ai_configs_provider_model", "provider", "model_name"),
	)

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
	scope = Column(String(16), nullable=False, default="user")
	created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	provider = Column(String(64), nullable=False)
	model_name = Column(String(128), nullable=False)
	api_key = Column(String(255), nullable=False)
	base_url = Column(String(255), nullable=True)
	temperature = Column(Float, nullable=False, default=0.3)
	system_prompt = Column(Text, nullable=True)
	repair_system_prompt = Column(Text, nullable=True)
	is_default = Column(Boolean, nullable=False, default=False)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	user = relationship("User", back_populates="ai_configs", foreign_keys=[user_id])
	creator = relationship("User", back_populates="created_ai_configs", foreign_keys=[created_by])


__all__ = ["AiConfig", "Role", "UserRole"]

__all__ = ["AiConfig", "Role", "UserRole"]
