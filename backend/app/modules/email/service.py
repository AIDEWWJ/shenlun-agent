"""邮件验证码与邮件发送业务层。"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.modules.auth.models import Role, User
from app.modules.email.repository import (
	create_email_config,
	create_email_template,
	create_verification_code,
	delete_email_config,
	delete_email_template,
	get_default_email_config,
	get_email_config,
	get_email_config_by_name,
	get_email_template,
	get_latest_verification_code,
	list_email_configs,
	list_email_templates,
	update_email_config,
	update_email_template,
)
from app.modules.auth.repository import (
	add_user_role,
	create_user,
	get_role_by_name,
	get_user_by_email,
	get_user_by_username,
	get_user_role_names,
	update_user_password,
)
from app.modules.auth.schemas import Token, UserRead
from app.modules.email.schemas import (
	EmailConfigCreate,
	EmailConfigListResponse,
	EmailConfigRead,
	EmailConfigUpdate,
	EmailTemplateCreate,
	EmailTemplateListResponse,
	EmailTemplateRead,
	EmailTemplateUpdate,
	ForgotPasswordConfirm,
	ForgotPasswordSendCode,
	RegisterConfirm,
	RegisterSendCode,
)

REGISTER_PURPOSE = "register_verify"
FORGOT_PASSWORD_PURPOSE = "forgot_password_verify"
DEFAULT_EXPIRE_MINUTES = 10


class _SafeFormatDict(dict):
	def __missing__(self, key):
		return ""


def _now() -> datetime:
	return datetime.now()


def _verification_expire_at() -> datetime:
	return _now() + timedelta(minutes=getattr(settings, "email_code_expire_minutes", DEFAULT_EXPIRE_MINUTES))


def _generate_code() -> str:
	return f"{secrets.randbelow(1_000_000):06d}"


def _hash_code(email: str, purpose: str, code: str) -> str:
	secret = settings.jwt_secret_key.encode("utf-8")
	message = f"{email}:{purpose}:{code}".encode("utf-8")
	return hmac.new(secret, message, hashlib.sha256).hexdigest()


def _build_context(data: dict) -> str:
	return json.dumps(data, ensure_ascii=False)


def _parse_context(context_json: str) -> dict:
	try:
		payload = json.loads(context_json)
		if isinstance(payload, dict):
			return payload
	except Exception:
		pass
	return {}


def _render_template(text: str, context: dict) -> str:
	return text.format_map(_SafeFormatDict(context))


def _render_email(template_key: str, context: dict) -> tuple[str, str, str | None]:
	template = get_email_template(context["db"], template_key)
	if template is None or not template.enabled:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮件模板未配置")
	variables = {
		"app_name": settings.app_name,
		"code": context["code"],
		"username": context.get("username", ""),
		"email": context["email"],
		"expires_minutes": getattr(settings, "email_code_expire_minutes", DEFAULT_EXPIRE_MINUTES),
	}
	subject = _render_template(template.subject, variables)
	body_text = _render_template(template.body_text, variables)
	body_html = _render_template(template.body_html, variables) if template.body_html else None
	return subject, body_text, body_html


def _send_smtp_email(db: Session, to_email: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
	config = get_default_email_config(db)
	if config is None or not config.enabled:
		return False

	message = EmailMessage()
	message["Subject"] = subject
	message["From"] = f"{config.sender_name} <{config.sender_email}>" if config.sender_name else config.sender_email
	message["To"] = to_email
	message.set_content(body_text)
	if body_html:
		message.add_alternative(body_html, subtype="html")

	try:
		if config.use_ssl:
			with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=15) as client:
				if config.smtp_username:
					client.login(config.smtp_username, config.smtp_password or "")
				client.send_message(message)
		else:
			with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as client:
				if config.use_tls:
					client.starttls()
				if config.smtp_username:
					client.login(config.smtp_username, config.smtp_password or "")
				client.send_message(message)
		return True
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"邮件发送失败：{exc}") from exc


def _persist_verification_code(db: Session, *, email: str, purpose: str, context: dict) -> str:
	code = _generate_code()
	code_hash = _hash_code(email, purpose, code)
	create_verification_code(
		db,
		email=email,
		purpose=purpose,
		code_hash=code_hash,
		context_json=_build_context(context),
		expires_at=_verification_expire_at(),
	)
	return code


def send_register_verification_code(db: Session, data: RegisterSendCode) -> None:
	"""发送注册验证码。"""

	if get_user_by_username(db, data.username):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
	if get_user_by_email(db, data.email):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在")

	code = _persist_verification_code(
		db,
		email=data.email,
		purpose=REGISTER_PURPOSE,
		context={
			"username": data.username,
			"email": data.email,
		},
	)
	try:
		_render_and_send(db, data.email, REGISTER_PURPOSE, code, data.username)
		db.commit()
	except Exception:
		db.rollback()
		raise


def confirm_register_verification(db: Session, data: RegisterConfirm) -> Token:
	"""校验注册验证码并创建账号。"""

	verification = _verify_code(db, email=data.email, purpose=REGISTER_PURPOSE, code=data.verification_code)
	context = _parse_context(verification.context_json)
	if context.get("username") != data.username:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码与账号信息不匹配")
	if context.get("email") != data.email:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码与邮箱不匹配")

	if get_user_by_username(db, data.username):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
	if get_user_by_email(db, data.email):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在")

	user = create_user(
		db,
		username=data.username,
		email=data.email,
		password_hash=get_password_hash(data.password),
		status="active",
	)
	learner_role = get_role_by_name(db, "learner")
	if learner_role is not None:
		add_user_role(db, user.id, learner_role.id)
	mark_code_used(db, verification)
	db.commit()
	return Token(access_token=create_access_token(subject=str(user.id)))


def send_forgot_password_verification_code(db: Session, data: ForgotPasswordSendCode) -> None:
	"""发送找回密码验证码。"""

	user = get_user_by_username(db, data.username)
	if user is None or user.email is None or user.email != data.email:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱不正确")

	code = _persist_verification_code(
		db,
		email=data.email,
		purpose=FORGOT_PASSWORD_PURPOSE,
		context={
			"username": data.username,
			"email": data.email,
			"user_id": user.id,
		},
	)
	try:
		_render_and_send(db, data.email, FORGOT_PASSWORD_PURPOSE, code, data.username)
		db.commit()
	except Exception:
		db.rollback()
		raise


def confirm_forgot_password(db: Session, data: ForgotPasswordConfirm) -> None:
	"""校验找回密码验证码并更新密码。"""

	verification = _verify_code(db, email=data.email, purpose=FORGOT_PASSWORD_PURPOSE, code=data.verification_code)
	context = _parse_context(verification.context_json)
	if context.get("username") != data.username:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码与账号信息不匹配")
	if context.get("email") != data.email:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码与邮箱不匹配")

	user = get_user_by_username(db, data.username)
	if user is None or user.email is None or user.email != data.email:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱不正确")

	update_user_password(db, user, get_password_hash(data.new_password))
	mark_code_used(db, verification)
	db.commit()


def _render_and_send(db: Session, email: str, purpose: str, code: str, username: str) -> None:
	template_key = purpose
	template = get_email_template(db, template_key)
	if template is None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮件模板未配置")
	config = get_default_email_config(db)
	if config is None or not config.enabled:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮件发送配置未启用")
	variables = {
		"db": db,
		"email": email,
		"purpose": purpose,
		"code": code,
		"username": username,
	}
	subject, body_text, body_html = _render_email(template_key, variables)
	_send_smtp_email(db, email, subject, body_text, body_html)


def _verify_code(db: Session, *, email: str, purpose: str, code: str):
	record = get_latest_verification_code(db, email=email, purpose=purpose)
	if record is None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码不存在")
	if record.used_at is not None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已使用")
	if record.expires_at < _now():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已过期")
	if record.code_hash != _hash_code(email, purpose, code):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
	return record


def mark_code_used(db: Session, verification) -> None:
	verification.used_at = _now()
	db.flush()


def list_email_config_read_models(db: Session, *, page: int = 1, page_size: int = 20) -> EmailConfigListResponse:
	items, total = list_email_configs(db, page=page, page_size=page_size)
	return EmailConfigListResponse(
		items=[EmailConfigRead.model_validate(item) for item in items],
		total=total,
		page=page,
		page_size=page_size,
	)


def _ensure_email_config_name_unique(db: Session, *, name: str, current_id: int | None = None) -> None:
	exists = get_email_config_by_name(db, name)
	if exists is not None and exists.id != current_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮件配置名称已存在")


def create_email_config_item(db: Session, data: EmailConfigCreate) -> EmailConfigRead:
	_ensure_email_config_name_unique(db, name=data.name)
	config = create_email_config(db, **data.model_dump())
	db.commit()
	db.refresh(config)
	return EmailConfigRead.model_validate(config)


def update_email_config_item(db: Session, config_id: int, data: EmailConfigUpdate) -> EmailConfigRead:
	config = get_email_config(db, config_id)
	if config is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邮件配置不存在")
	update_data = data.model_dump(exclude_unset=True)
	if "name" in update_data and update_data["name"] is not None:
		_ensure_email_config_name_unique(db, name=update_data["name"], current_id=config.id)
	update_email_config(db, config, **update_data)
	db.commit()
	db.refresh(config)
	return EmailConfigRead.model_validate(config)


def delete_email_config_item(db: Session, config_id: int) -> None:
	config = get_email_config(db, config_id)
	if config is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邮件配置不存在")
	delete_email_config(db, config)
	db.commit()


def list_email_template_read_models(db: Session, *, page: int = 1, page_size: int = 20) -> EmailTemplateListResponse:
	items, total = list_email_templates(db, page=page, page_size=page_size)
	return EmailTemplateListResponse(
		items=[EmailTemplateRead.model_validate(item) for item in items],
		total=total,
		page=page,
		page_size=page_size,
	)


def create_email_template_item(db: Session, data: EmailTemplateCreate) -> EmailTemplateRead:
	if get_email_template(db, data.template_key) is not None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮件模板键已存在")
	template = create_email_template(db, **data.model_dump())
	db.commit()
	db.refresh(template)
	return EmailTemplateRead.model_validate(template)


def update_email_template_item(db: Session, template_key: str, data: EmailTemplateUpdate) -> EmailTemplateRead:
	template = get_email_template(db, template_key)
	if template is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邮件模板不存在")
	update_email_template(db, template, **data.model_dump(exclude_unset=True))
	db.commit()
	db.refresh(template)
	return EmailTemplateRead.model_validate(template)


def delete_email_template_item(db: Session, template_key: str) -> None:
	template = get_email_template(db, template_key)
	if template is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邮件模板不存在")
	delete_email_template(db, template)
	db.commit()
