"""用户业务层。

这里放用户相关的业务逻辑。
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.repositories.user_repo import (
	create_user,
	delete_user,
	get_user_by_email,
	get_user_by_id,
	get_user_by_username,
	get_user_role_names,
	list_users,
	set_user_roles,
	update_user_password,
	update_user_profile,
)
from app.schemas.admin_user import AdminUserCreate, AdminUserRead, AdminUserUpdate
from app.services.auth_service import build_user_profile


def _ensure_user_unique(db: Session, *, user_id: int | None = None, username: str | None = None, email: str | None = None) -> None:
	"""检查用户名和邮箱是否唯一。"""

	if username is not None:
		exists = get_user_by_username(db, username)
		if exists is not None and exists.id != user_id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

	if email is not None:
		exists = get_user_by_email(db, email)
		if exists is not None and exists.id != user_id:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在")


def list_admin_users(db: Session) -> list[AdminUserRead]:
	"""查询用户列表。"""

	return [build_user_profile(db, user) for user in list_users(db)]


def get_admin_user(db: Session, user_id: int) -> AdminUserRead:
	"""查询单个用户。"""

	user = get_user_by_id(db, user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
	return build_user_profile(db, user)


def create_admin_user(db: Session, data: AdminUserCreate) -> AdminUserRead:
	"""管理员创建用户。"""

	_ensure_user_unique(db, username=data.username, email=data.email)
	user = create_user(
		db,
		username=data.username,
		email=data.email,
		password_hash=get_password_hash(data.password),
		status=data.status,
	)
	try:
		set_user_roles(db, user.id, data.roles)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
	db.commit()
	db.refresh(user)
	return build_user_profile(db, user)


def update_admin_user(db: Session, user_id: int, data: AdminUserUpdate) -> AdminUserRead:
	"""管理员更新用户。"""

	user = get_user_by_id(db, user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

	update_data = data.model_dump(exclude_unset=True)

	if "username" in update_data or "email" in update_data:
		_ensure_user_unique(
			db,
			user_id=user.id,
			username=update_data.get("username"),
			email=update_data.get("email"),
		)

	if "password" in update_data and update_data["password"]:
		update_user_password(db, user, get_password_hash(update_data["password"]))

	update_user_profile(
		db,
		user,
		username=update_data.get("username"),
		email=update_data.get("email"),
	)

	if "status" in update_data and update_data["status"] is not None:
		user.status = update_data["status"]

	if "roles" in update_data and update_data["roles"] is not None:
		try:
			set_user_roles(db, user.id, update_data["roles"])
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	db.commit()
	db.refresh(user)
	return build_user_profile(db, user)


def delete_admin_user(db: Session, user_id: int) -> None:
	"""管理员删除用户。"""

	user = get_user_by_id(db, user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

	delete_user(db, user)
	db.commit()
