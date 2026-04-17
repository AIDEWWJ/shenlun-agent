from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    ai_configs = relationship("AiConfig", back_populates="user", foreign_keys="AiConfig.user_id")
    created_ai_configs = relationship(
        "AiConfig",
        back_populates="creator",
        foreign_keys="AiConfig.created_by",
    )
    questions = relationship("Question", back_populates="user", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="user", cascade="all, delete-orphan")
    practice_records = relationship(
        "PracticeRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    prompt_templates = relationship(
        "PromptTemplate",
        back_populates="user",
        cascade="all, delete-orphan",
    )
