from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.response import api_success
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.practice import ReviewCreateRequest
from app.services.practice_service import review_answer as review_answer_service

router = APIRouter(tags=["practice"])


@router.post("/analyze", response_model=ApiResponse)
def analyze_question(current_user: User = Depends(get_current_active_user)):
    return api_success({"user_id": current_user.id, "username": current_user.username}, message="分析接口待实现")


@router.post("/outline", response_model=ApiResponse)
def generate_outline(current_user: User = Depends(get_current_active_user)):
    return api_success({"user_id": current_user.id, "username": current_user.username}, message="提纲接口待实现")


@router.post("/review", response_model=ApiResponse)
def review_answer(
    data: ReviewCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    result = review_answer_service(
        db,
        user_id=current_user.id,
        question_id=data.question_id,
        answer_id=data.answer_id,
        reference_points=data.reference_points,
        use_llm=data.use_llm,
    )
    return api_success(result, message="批改完成")
