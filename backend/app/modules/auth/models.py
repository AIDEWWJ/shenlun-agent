from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
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


class Role(Base):
	__tablename__ = "roles"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(64), unique=True, nullable=False, index=True)
	display_name = Column(String(128), nullable=False)
	description = Column(String(255), nullable=True)

	user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base):
	__tablename__ = "user_roles"
	__table_args__ = (
		UniqueConstraint("user_id", "role_id", name="uk_user_role"),
		Index("idx_user_roles_role_id", "role_id"),
	)

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

	user = relationship("User", back_populates="user_roles")
	role = relationship("Role", back_populates="user_roles")


__all__ = ["User", "Role", "UserRole"]
