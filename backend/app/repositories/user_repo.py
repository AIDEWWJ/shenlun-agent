"""用户数据访问层。

这里放 User 相关的数据库访问逻辑。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, User, UserRole


def get_user_by_username(db: Session, username: str) -> User | None:
	"""根据用户名获取用户。"""

	return db.scalars(select(User).where(User.username == username)).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
	"""根据用户 ID 获取用户。"""

	return db.get(User, user_id)


def list_users(db: Session) -> list[User]:
	"""获取用户列表。"""

	return db.scalars(select(User).order_by(User.id.desc())).all()


def get_user_by_email(db: Session, email: str) -> User | None:
	"""根据邮箱获取用户。"""

	return db.scalars(select(User).where(User.email == email)).first()


def update_user_profile(db: Session, user: User, *, username: str | None = None, email: str | None = None) -> User:
	"""更新用户基础资料。"""

	if username is not None:
		user.username = username
	if email is not None:
		user.email = email
	db.flush()
	return user


def update_user_password(db: Session, user: User, password_hash: str) -> User:
	"""更新用户密码。"""

	user.password_hash = password_hash
	db.flush()
	return user


def create_user(
	db: Session,
	*,
	username: str,
	email: str | None,
	password_hash: str,
	status: str = "active",
) -> User:
	"""创建用户。"""

	user = User(
		username=username,
		email=email,
		password_hash=password_hash,
		status=status,
	)
	db.add(user)
	db.flush()
	return user


def get_role_by_name(db: Session, role_name: str) -> Role | None:
	"""根据角色名获取角色。"""

	return db.scalars(select(Role).where(Role.name == role_name)).first()


def get_roles_by_names(db: Session, role_names: list[str]) -> list[Role]:
	"""根据角色名列表获取角色。"""

	if not role_names:
		return []
	return db.scalars(select(Role).where(Role.name.in_(role_names))).all()


def add_user_role(db: Session, user_id: int, role_id: int) -> UserRole:
	"""给用户绑定角色。"""

	user_role = UserRole(user_id=user_id, role_id=role_id)
	db.add(user_role)
	db.flush()
	return user_role


def clear_user_roles(db: Session, user_id: int) -> None:
	"""清空用户的所有角色。"""

	db.query(UserRole).filter(UserRole.user_id == user_id).delete(synchronize_session=False)
	db.flush()


def set_user_roles(db: Session, user_id: int, role_names: list[str]) -> list[str]:
	"""按角色名重置用户角色。"""

	clear_user_roles(db, user_id)
	unique_role_names = list(dict.fromkeys(role_names))
	roles = get_roles_by_names(db, unique_role_names)
	if len(roles) != len(unique_role_names):
		existing_names = {role.name for role in roles}
		missing_names = [name for name in unique_role_names if name not in existing_names]
		raise ValueError(f"角色不存在：{', '.join(missing_names)}")
	for role in roles:
		add_user_role(db, user_id, role.id)
	return [role.name for role in roles]


def delete_user(db: Session, user: User) -> None:
	"""删除用户。"""

	db.delete(user)
	db.flush()


def get_user_role_names(db: Session, user_id: int) -> list[str]:
	"""获取用户的角色名列表。"""

	return db.scalars(
		select(Role.name)
		.join(UserRole, UserRole.role_id == Role.id)
		.where(UserRole.user_id == user_id)
	).all()
