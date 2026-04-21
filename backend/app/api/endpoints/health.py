from fastapi import APIRouter

from app.core.response import api_success
from app.schemas.common import ApiResponse


router = APIRouter(tags=["system"])


@router.get("/health", response_model=ApiResponse)
def health_check():
    return api_success({"status": "ok"}, message="服务运行正常")

