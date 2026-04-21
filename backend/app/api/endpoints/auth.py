from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.response import api_success
from app.models import User
from app.schemas.auth import PasswordChange, PasswordReset, UserCreate, UserLogin, UserProfileUpdate
from app.schemas.email import (
    ForgotPasswordConfirm,
    ForgotPasswordSendCode,
    RegisterConfirm,
    RegisterSendCode,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import (
    build_user_profile,
    change_current_user_password,
    login_user,
    update_current_user,
)
from app.services.email_service import (
    confirm_forgot_password,
    confirm_register_verification,
    send_forgot_password_verification_code,
    send_register_verification_code,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/send-code", response_model=ApiResponse)
def register_send_code(data: RegisterSendCode, db: Session = Depends(get_db)):
    send_register_verification_code(db, data)
    return api_success(message="验证码已发送")


@router.post("/register", response_model=ApiResponse)
def register(data: RegisterConfirm, db: Session = Depends(get_db)):
    return api_success(confirm_register_verification(db, data), message="注册成功")


@router.post("/login", response_model=ApiResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    return api_success(login_user(db, data), message="登录成功")


@router.get("/me", response_model=ApiResponse)
def me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return api_success(build_user_profile(db, current_user), message="获取用户信息成功")


@router.put("/me", response_model=ApiResponse)
def update_me(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return api_success(update_current_user(db, current_user, data), message="更新个人资料成功")


@router.post("/me/password", response_model=ApiResponse)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    change_current_user_password(db, current_user, data)
    return api_success(message="密码修改成功")


@router.post("/forgot-password/send-code", response_model=ApiResponse)
def forgot_password_send_code(data: ForgotPasswordSendCode, db: Session = Depends(get_db)):
    send_forgot_password_verification_code(db, data)
    return api_success(message="验证码已发送")


@router.post("/forgot-password", response_model=ApiResponse)
def forgot_password(data: ForgotPasswordConfirm, db: Session = Depends(get_db)):
    confirm_forgot_password(db, data)
    return api_success(message="密码重置成功")
