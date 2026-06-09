"""认证业务模块。"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.modules.auth.repository import (
	add_user_role,
	create_user,
	get_role_by_name,
	get_user_by_email,
	get_user_by_username,
	get_user_role_names,
	update_user_password,
	update_user_profile,
)
from app.modules.auth.schemas import PasswordChange, PasswordReset, Token, UserCreate, UserLogin, UserProfileUpdate, UserRead


def register_user(db: Session, data: UserCreate) -> UserRead:
	"""注册用户并自动分配学员角色。"""

	if get_user_by_username(db, data.username):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

	if data.email and get_user_by_email(db, data.email):
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

	db.commit()
	db.refresh(user)

	return UserRead(
		id=user.id,
		username=user.username,
		email=user.email,
		status=user.status,
		created_at=user.created_at,
		roles=get_user_role_names(db, user.id),
	)


def login_user(db: Session, data: UserLogin) -> Token:
	"""校验用户名和密码并签发访问令牌。"""

	user = get_user_by_username(db, data.username)
	if user is None or not verify_password(data.password, user.password_hash):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

	token = create_access_token(subject=str(user.id))
	return Token(access_token=token)


def build_user_profile(db: Session, user) -> UserRead:
	"""把数据库用户对象转换为接口返回结构。"""

	return UserRead(
		id=user.id,
		username=user.username,
		email=user.email,
		status=user.status,
		created_at=user.created_at,
		roles=get_user_role_names(db, user.id),
	)


def update_current_user(db: Session, current_user, data: UserProfileUpdate) -> UserRead:
	"""更新当前用户的基础资料。"""

	if data.username is not None:
		exists = get_user_by_username(db, data.username)
		if exists is not None and exists.id != current_user.id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

	if data.email is not None:
		exists = get_user_by_email(db, data.email)
		if exists is not None and exists.id != current_user.id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在")

	update_user_profile(db, current_user, username=data.username, email=data.email)
	db.commit()
	db.refresh(current_user)
	return build_user_profile(db, current_user)


def change_current_user_password(db: Session, current_user, data: PasswordChange) -> None:
	"""修改当前用户密码。"""

	if not verify_password(data.current_password, current_user.password_hash):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误")

	update_user_password(db, current_user, get_password_hash(data.new_password))
	db.commit()


def reset_password_by_identity(db: Session, data: PasswordReset) -> None:
	"""通过用户名和邮箱重置密码。"""

	user = get_user_by_username(db, data.username)
	if user is None or user.email is None or user.email != data.email:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱不正确")

	update_user_password(db, user, get_password_hash(data.new_password))
	db.commit()


__all__ = [
	"register_user",
	"login_user",
	"build_user_profile",
	"update_current_user",
	"change_current_user_password",
	"reset_password_by_identity",
]
