from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class AiConfig(Base):
    __tablename__ = "ai_configs"

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
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="ai_configs", foreign_keys=[user_id])
    creator = relationship("User", back_populates="created_ai_configs", foreign_keys=[created_by])
