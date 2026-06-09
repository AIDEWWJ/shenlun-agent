"""Dashboard、统计、推荐与对比接口。"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.response import api_success
from app.modules.auth.models import User
from app.modules.dashboard.service import (
    compare_reviews,
    get_latest_answer,
    get_question_type_stats,
    get_random_question_for_user,
    get_recommendations,
    get_trend,
    get_user_dashboard,
)
from app.modules.question.schemas import QuestionRead
from app.shared.deps import get_current_active_user, get_db
from app.shared.schemas import ApiResponse


router = APIRouter(tags=["用户-学习概览与统计"])


@router.get("/dashboard/me", response_model=ApiResponse, summary="获取学习概览")
def dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的学习概览信息，包括练习总数、平均分、连续天数、薄弱题型等。"""
    return api_success(get_user_dashboard(db, current_user.id), message="获取学习概览成功")


@router.get("/stats/by-question-type", response_model=ApiResponse, summary="按题型统计")
def stats_by_question_type(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取用户在各题型下的练习与得分统计。"""
    return api_success(
        get_question_type_stats(db, current_user.id, date_from=date_from, date_to=date_to),
        message="获取题型统计成功",
    )


@router.get("/stats/trend", response_model=ApiResponse, summary="得分趋势")
def stats_trend(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取用户得分趋势（按天聚合）。"""
    return api_success(
        get_trend(db, current_user.id, date_from=date_from, date_to=date_to),
        message="获取得分趋势成功",
    )


@router.get("/questions/random", response_model=ApiResponse, summary="随机抽题")
def random_question(
    question_type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    source: str | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按筛选条件随机返回 1 道题目。"""
    question = get_random_question_for_user(
        db,
        current_user.id,
        question_type=question_type,
        tag=tag,
        source=source,
    )
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="没有符合条件的题目")

    from app.modules.question.service import _to_read_model
    return api_success(_to_read_model(question), message="随机抽题成功")


@router.get("/questions/recommendations", response_model=ApiResponse, summary="推荐题目")
def recommendations(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """根据用户历史练习情况推荐题目，优先推荐薄弱题型和未练习的题目。"""
    return api_success(
        get_recommendations(db, current_user.id, limit=limit),
        message="获取推荐题目成功",
    )


@router.get("/questions/{question_id}/latest-answer", response_model=ApiResponse, summary="获取某题最近答案")
def latest_answer(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取当前用户在某道题上的最近一次答案版本。"""
    result = get_latest_answer(db, current_user.id, question_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该题目暂无答案记录")
    return api_success(result, message="获取最近答案成功")


@router.get("/reviews/{review_id}/compare/{target_review_id}", response_model=ApiResponse, summary="批改结果对比")
def review_compare(
    review_id: int,
    target_review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """对比两次批改结果，返回分数差异、维度变化、问题增减等。"""
    return api_success(
        compare_reviews(db, current_user.id, review_id, target_review_id),
        message="获取批改对比成功",
    )
