"""Dashboard 业务服务。"""

from __future__ import annotations

import json
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.repository import get_user_role_names
from app.modules.dashboard.repository import (
    count_user_practices,
    count_user_reviews,
    get_latest_answer_for_question,
    get_random_question,
    get_recent_practice_items,
    get_recommended_questions,
    get_review_for_compare,
    get_score_trend,
    get_stats_by_question_type,
    get_user_score_stats,
    get_user_streak_days,
    get_weak_question_types,
)
from app.modules.dashboard.schemas import (
    DashboardResponse,
    QuestionTypeStats,
    RecentPracticeItem,
    RecommendationItem,
    RecommendationResponse,
    ReviewCompareResponse,
    StatsResponse,
    TrendItem,
    TrendResponse,
)
from app.modules.practice.models import Answer
from app.modules.practice.repository import get_review_by_answer_id
from app.modules.question.models import Question


def _is_admin(db: Session, user_id: int) -> bool:
    return "admin" in get_user_role_names(db, user_id)


def get_user_dashboard(db: Session, user_id: int) -> DashboardResponse:
    """获取用户学习概览。"""
    total_practices = count_user_practices(db, user_id)
    total_reviews = count_user_reviews(db, user_id)
    score_stats = get_user_score_stats(db, user_id)
    streak_days = get_user_streak_days(db, user_id)
    weak_types = get_weak_question_types(db, user_id)
    recent_items = get_recent_practice_items(db, user_id)

    return DashboardResponse(
        total_practices=total_practices,
        total_reviews=total_reviews,
        avg_score=score_stats["avg_score"],
        latest_score=score_stats["latest_score"],
        best_score=score_stats["best_score"],
        streak_days=streak_days,
        weak_question_types=weak_types,
        recent_items=[
            RecentPracticeItem(
                record_id=item["record_id"],
                question_id=item["question_id"],
                question_title=item["question_title"],
                question_type=item["question_type"],
                score=item["score"],
                created_at=item["created_at"],
            )
            for item in recent_items
        ],
    )


def get_question_type_stats(
    db: Session,
    user_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> StatsResponse:
    """按题型统计。"""
    items = get_stats_by_question_type(db, user_id, date_from=date_from, date_to=date_to)
    return StatsResponse(
        items=[
            QuestionTypeStats(
                question_type=item["question_type"],
                count=item["count"],
                avg_score=item["avg_score"],
                best_score=item["best_score"],
                latest_score=item["latest_score"],
            )
            for item in items
        ]
    )


def get_random_question_for_user(
    db: Session,
    user_id: int,
    *,
    question_type: str | None = None,
    tag: str | None = None,
    source: str | None = None,
) -> Question | None:
    """随机抽题。"""
    return get_random_question(db, user_id, question_type=question_type, tag=tag, source=source)


def get_recommendations(
    db: Session,
    user_id: int,
    *,
    limit: int = 5,
) -> RecommendationResponse:
    """获取推荐题目。"""
    items = get_recommended_questions(db, user_id, limit=limit)
    return RecommendationResponse(
        items=[
            RecommendationItem(
                question_id=item["question_id"],
                title=item["title"],
                question_type=item["question_type"],
                tags=item["tags"],
                reason=item["reason"],
            )
            for item in items
        ]
    )


def get_trend(
    db: Session,
    user_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> TrendResponse:
    """获取得分趋势。"""
    items = get_score_trend(db, user_id, date_from=date_from, date_to=date_to)
    return TrendResponse(
        items=[
            TrendItem(
                date=item["date"],
                count=item["count"],
                avg_score=item["avg_score"],
            )
            for item in items
        ]
    )


def get_latest_answer(db: Session, user_id: int, question_id: int) -> dict | None:
    """获取某题最近答案。"""
    answer = get_latest_answer_for_question(db, user_id, question_id)
    if answer is None:
        return None
    review = get_review_by_answer_id(db, answer.id)
    return {
        "answer_id": answer.id,
        "version_no": answer.version_no,
        "content": answer.content,
        "reviewed": review is not None,
        "review_id": review.id if review else None,
        "created_at": answer.created_at,
    }


def compare_reviews(
    db: Session,
    user_id: int,
    base_review_id: int,
    target_review_id: int,
) -> ReviewCompareResponse:
    """对比两次批改结果。"""
    base_review = get_review_for_compare(db, base_review_id)
    if base_review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基准批改记录不存在")
    if base_review.user_id != user_id and not _is_admin(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该批改记录")

    target_review = get_review_for_compare(db, target_review_id)
    if target_review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对比批改记录不存在")
    if target_review.user_id != user_id and not _is_admin(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该批改记录")

    base_score = base_review.score
    target_score = target_review.score
    score_diff = (target_score or 0) - (base_score or 0)

    # 解析 issues
    base_issues = set(base_review.issues.splitlines()) if base_review.issues else set()
    target_issues = set(target_review.issues.splitlines()) if target_review.issues else set()
    issues_added = list(target_issues - base_issues)
    issues_resolved = list(base_issues - target_issues)

    # 解析 suggestions
    base_suggestions = set(base_review.suggestions.splitlines()) if base_review.suggestions else set()
    target_suggestions = set(target_review.suggestions.splitlines()) if target_review.suggestions else set()
    suggestion_changes = list(target_suggestions - base_suggestions)

    # 维度对比
    def _parse_score_breakdown(json_str: str | None) -> dict:
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except Exception:
            return {}

    base_breakdown = _parse_score_breakdown(base_review.score_breakdown_json)
    target_breakdown = _parse_score_breakdown(target_review.score_breakdown_json)
    all_dims = set(list(base_breakdown.keys()) + list(target_breakdown.keys()))
    dimension_diffs = []
    for dim in sorted(all_dims):
        base_val = base_breakdown.get(dim, 0)
        target_val = target_breakdown.get(dim, 0)
        if base_val != target_val:
            dimension_diffs.append({
                "dimension": dim,
                "base_score": base_val,
                "target_score": target_val,
                "diff": target_val - base_val,
            })

    return ReviewCompareResponse(
        base_review_id=base_review_id,
        target_review_id=target_review_id,
        score_diff=score_diff,
        base_score=base_score,
        target_score=target_score,
        dimension_diffs=dimension_diffs,
        issues_added=issues_added,
        issues_resolved=issues_resolved,
        suggestion_changes=suggestion_changes,
    )
