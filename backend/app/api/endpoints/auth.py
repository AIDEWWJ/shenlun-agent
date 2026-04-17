from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import Role, User, UserRole
from app.schemas.auth import Token, UserCreate, UserLogin, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


def _get_user_role_names(db: Session, user_id: int) -> list[str]:
    return db.scalars(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    ).all()


@router.post("/register", response_model=UserRead)
def register(data: UserCreate, db: Session = Depends(get_db)):
    user_exists = db.scalars(select(User).where(User.username == data.username)).first()
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    if data.email:
        email_exists = db.scalars(select(User).where(User.email == data.email)).first()
        if email_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=get_password_hash(data.password),
        status="active",
    )
    db.add(user)
    db.flush()

    learner_role = db.scalars(select(Role).where(Role.name == "learner")).first()
    if learner_role is not None:
        db.add(UserRole(user_id=user.id, role_id=learner_role.id))

    db.commit()
    db.refresh(user)

    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        created_at=user.created_at,
        roles=_get_user_role_names(db, user.id),
    )


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.scalars(select(User).where(User.username == data.username)).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token(subject=user.username)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        status=current_user.status,
        created_at=current_user.created_at,
        roles=_get_user_role_names(db, current_user.id),
    )
