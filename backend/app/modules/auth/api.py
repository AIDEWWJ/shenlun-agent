from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.auth.service import (
	build_user_profile,
	change_current_user_password,
	login_user,
	update_current_user,
)
from app.modules.email.service import (
	confirm_forgot_password,
	confirm_register_verification,
	send_forgot_password_verification_code,
	send_register_verification_code,
)
from app.shared.deps import get_current_active_user, get_db
from app.modules.auth.schemas import PasswordChange, UserLogin, UserProfileUpdate
from app.shared.schemas import ApiResponse
from app.modules.email.schemas import ForgotPasswordConfirm, ForgotPasswordSendCode, RegisterConfirm, RegisterSendCode


router = APIRouter(prefix="/auth", tags=["用户-认证与账户"])


@router.post("/register/send-code", response_model=ApiResponse, summary="发送注册验证码")
def register_send_code(data: RegisterSendCode, db: Session = Depends(get_db)):
	"""向注册邮箱发送验证码。注册前会先校验用户名和邮箱是否可用。"""
	send_register_verification_code(db, data)
	return api_success(message="验证码已发送")


@router.post("/register", response_model=ApiResponse, summary="注册账号")
def register(data: RegisterConfirm, db: Session = Depends(get_db)):
	"""校验注册验证码并创建账号，成功后直接返回登录令牌。"""
	return api_success(confirm_register_verification(db, data), message="注册成功")


@router.post("/login", response_model=ApiResponse, summary="登录")
def login(data: UserLogin, db: Session = Depends(get_db)):
	"""使用用户名和密码登录，成功后返回 Bearer Token。"""
	return api_success(login_user(db, data), message="登录成功")


@router.get("/me", response_model=ApiResponse, summary="获取当前用户信息")
def me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
	"""获取当前登录用户的基础信息和角色列表。"""
	return api_success(build_user_profile(db, current_user), message="获取用户信息成功")


@router.put("/me", response_model=ApiResponse, summary="更新当前用户资料")
def update_me(
	data: UserProfileUpdate,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""更新当前登录用户的用户名或邮箱。"""
	return api_success(update_current_user(db, current_user, data), message="更新个人资料成功")


@router.post("/me/password", response_model=ApiResponse, summary="修改当前用户密码")
def change_password(
	data: PasswordChange,
	current_user: User = Depends(get_current_active_user),
	db: Session = Depends(get_db),
):
	"""在已登录状态下修改当前用户密码。"""
	change_current_user_password(db, current_user, data)
	return api_success(message="密码修改成功")


@router.post("/forgot-password/send-code", response_model=ApiResponse, summary="发送找回密码验证码")
def forgot_password_send_code(data: ForgotPasswordSendCode, db: Session = Depends(get_db)):
	"""向已绑定邮箱发送找回密码验证码。"""
	send_forgot_password_verification_code(db, data)
	return api_success(message="验证码已发送")


@router.post("/forgot-password", response_model=ApiResponse, summary="重置密码")
def forgot_password(data: ForgotPasswordConfirm, db: Session = Depends(get_db)):
	"""校验找回密码验证码并重置账号密码。"""
	confirm_forgot_password(db, data)
	return api_success(message="密码重置成功")
