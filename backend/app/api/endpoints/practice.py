from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user
from app.models import User

router = APIRouter(tags=["practice"])


@router.post("/analyze")
def analyze_question(current_user: User = Depends(get_current_active_user)):
    return {
        "success": True,
        "message": "分析接口待实现",
        "data": {"user_id": current_user.id, "username": current_user.username},
    }


@router.post("/outline")
def generate_outline(current_user: User = Depends(get_current_active_user)):
    return {
        "success": True,
        "message": "提纲接口待实现",
        "data": {"user_id": current_user.id, "username": current_user.username},
    }


@router.post("/review")
def review_answer(current_user: User = Depends(get_current_active_user)):
    return {
        "success": True,
        "message": "批改接口待实现",
        "data": {"user_id": current_user.id, "username": current_user.username},
    }
