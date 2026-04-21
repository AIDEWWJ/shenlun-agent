"""邮件相关数据访问层。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmailConfig, EmailTemplate, EmailVerificationCode


def list_email_configs(db: Session) -> list[EmailConfig]:
	return db.scalars(select(EmailConfig).order_by(EmailConfig.id.desc())).all()


def get_email_config(db: Session, config_id: int) -> EmailConfig | None:
	return db.get(EmailConfig, config_id)


def get_default_email_config(db: Session) -> EmailConfig | None:
	return db.scalars(select(EmailConfig).where(EmailConfig.enabled.is_(True)).order_by(EmailConfig.id.asc())).first()


def create_email_config(db: Session, **data) -> EmailConfig:
	config = EmailConfig(**data)
	db.add(config)
	db.flush()
	return config


def update_email_config(db: Session, config: EmailConfig, **data) -> EmailConfig:
	for key, value in data.items():
		if value is not None:
			setattr(config, key, value)
	db.flush()
	return config


def delete_email_config(db: Session, config: EmailConfig) -> None:
	db.delete(config)
	db.flush()


def list_email_templates(db: Session) -> list[EmailTemplate]:
	return db.scalars(select(EmailTemplate).order_by(EmailTemplate.id.asc())).all()


def get_email_template(db: Session, template_key: str) -> EmailTemplate | None:
	return db.scalars(select(EmailTemplate).where(EmailTemplate.template_key == template_key)).first()


def create_email_template(db: Session, **data) -> EmailTemplate:
	template = EmailTemplate(**data)
	db.add(template)
	db.flush()
	return template


def update_email_template(db: Session, template: EmailTemplate, **data) -> EmailTemplate:
	for key, value in data.items():
		if value is not None:
			setattr(template, key, value)
	db.flush()
	return template


def delete_email_template(db: Session, template: EmailTemplate) -> None:
	db.delete(template)
	db.flush()


def create_verification_code(db: Session, **data) -> EmailVerificationCode:
	code = EmailVerificationCode(**data)
	db.add(code)
	db.flush()
	return code


def get_latest_verification_code(db: Session, *, email: str, purpose: str) -> EmailVerificationCode | None:
	return db.scalars(
		select(EmailVerificationCode)
		.where(
			EmailVerificationCode.email == email,
			EmailVerificationCode.purpose == purpose,
		)
		.order_by(EmailVerificationCode.id.desc())
	).first()
