from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text, func

from app.db.base import Base


class EmailConfig(Base):
	"""邮件发送配置。"""

	__tablename__ = "email_configs"
	__table_args__ = (
		Index("idx_email_configs_enabled_id", "enabled", "id"),
	)

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(64), unique=True, nullable=False, default="default")
	smtp_host = Column(String(255), nullable=False)
	smtp_port = Column(Integer, nullable=False, default=587)
	smtp_username = Column(String(255), nullable=True)
	smtp_password = Column(String(255), nullable=True)
	sender_email = Column(String(128), nullable=False)
	sender_name = Column(String(128), nullable=True)
	use_tls = Column(Boolean, nullable=False, default=True)
	use_ssl = Column(Boolean, nullable=False, default=False)
	enabled = Column(Boolean, nullable=False, default=True)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)
	updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class EmailTemplate(Base):
	"""邮件模板。"""

	__tablename__ = "email_templates"

	id = Column(Integer, primary_key=True, index=True)
	template_key = Column(String(64), unique=True, nullable=False, index=True)
	template_name = Column(String(128), nullable=False)
	subject = Column(String(255), nullable=False)
	body_text = Column(Text, nullable=False)
	body_html = Column(Text, nullable=True)
	enabled = Column(Boolean, nullable=False, default=True)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)
	updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class EmailVerificationCode(Base):
	"""邮件验证码记录。"""

	__tablename__ = "email_verification_codes"
	__table_args__ = (
		Index("idx_email_verification_email_purpose_id", "email", "purpose", "id"),
		Index("idx_email_verification_expires_at", "expires_at"),
	)

	id = Column(Integer, primary_key=True, index=True)
	email = Column(String(128), nullable=False)
	purpose = Column(String(32), nullable=False)
	code_hash = Column(String(255), nullable=False)
	context_json = Column(Text, nullable=False)
	expires_at = Column(DateTime, nullable=False)
	used_at = Column(DateTime, nullable=True)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)


__all__ = ["EmailConfig", "EmailTemplate", "EmailVerificationCode"]

__all__ = ["EmailConfig", "EmailTemplate", "EmailVerificationCode"]
