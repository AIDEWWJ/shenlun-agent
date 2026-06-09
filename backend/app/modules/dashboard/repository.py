"""Dashboard 数据查询。"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.modules.practice.models import Answer, PracticeRecord
from app.modules.question.models import Question
from app.modules.review.models import Review


def count_user_practices(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count(PracticeRecord.id)).where(PracticeRecord.user_id == user_id)
    ) or 0


def count_user_reviews(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count(Review.id)).where(Review.user_id == user_id)
    ) or 0


def get_user_score_stats(db: Session, user_id: int) -> dict:
    """获取用户分数统计：平均分、最高分、最近分。"""
    row = db.execute(
        select(
            func.avg(Review.score),
            func.max(Review.score),
        ).where(Review.user_id == user_id, Review.score.isnot(None))
    ).first()

    latest_score = db.scalar(
        select(Review.score)
        .where(Review.user_id == user_id, Review.score.isnot(None))
        .order_by(Review.created_at.desc(), Review.id.desc())
        .limit(1)
    )

    avg_score = round(float(row[0]), 1) if row and row[0] is not None else None
    best_score = int(row[1]) if row and row[1] is not None else None

    return {
        "avg_score": avg_score,
        "best_score": best_score,
        "latest_score": int(latest_score) if latest_score is not None else None,
    }


def get_user_streak_days(db: Session, user_id: int) -> int:
    """计算用户连续练习天数（从今天往前推）。"""
    today = date.today()
    # 获取用户最近 60 天内有练习的日期
    rows = db.execute(
        select(func.date(PracticeRecord.created_at))
        .where(
            PracticeRecord.user_id == user_id,
            PracticeRecord.created_at >= datetime.combine(today - timedelta(days=60), time.min),
        )
        .group_by(func.date(PracticeRecord.created_at))
        .order_by(func.date(PracticeRecord.created_at).desc())
    ).scalars().all()

    if not rows:
        return 0

    practice_dates = set()
    for row in rows:
        if isinstance(row, str):
            practice_dates.add(row)
        elif isinstance(row, date):
            practice_dates.add(row.isoformat())
        else:
            practice_dates.add(str(row))

    streak = 0
    check_date = today
    # 如果今天没有练习，从昨天开始算
    if check_date.isoformat() not in practice_dates:
        check_date = today - timedelta(days=1)

    while check_date.isoformat() in practice_dates:
        streak += 1
        check_date -= timedelta(days=1)

    return streak


def get_weak_question_types(db: Session, user_id: int, limit: int = 3) -> list[str]:
    """获取用户薄弱题型（平均分最低的题型）。"""
    rows = db.execute(
        select(
            Review.question_type_snapshot,
            func.avg(Review.score),
        )
        .where(
            Review.user_id == user_id,
            Review.score.isnot(None),
            Review.question_type_snapshot.isnot(None),
            Review.question_type_snapshot != "",
        )
        .group_by(Review.question_type_snapshot)
        .having(func.count(Review.id) >= 1)
        .order_by(func.avg(Review.score).asc())
        .limit(limit)
    ).all()

    return [row[0] for row in rows if row[0]]


def get_recent_practice_items(db: Session, user_id: int, limit: int = 5) -> list[dict]:
    """获取最近练习记录。"""
    records = db.execute(
        select(
            PracticeRecord.id,
            PracticeRecord.question_id,
            PracticeRecord.created_at,
            Question.title,
            Question.question_type,
            Review.score,
        )
        .join(Question, PracticeRecord.question_id == Question.id)
        .outerjoin(Review, PracticeRecord.review_id == Review.id)
        .where(PracticeRecord.user_id == user_id)
        .order_by(PracticeRecord.id.desc())
        .limit(limit)
    ).all()

    return [
        {
            "record_id": row[0],
            "question_id": row[1],
            "created_at": row[2],
            "question_title": row[3] or "",
            "question_type": row[4],
            "score": row[5],
        }
        for row in records
    ]


def get_stats_by_question_type(
    db: Session,
    user_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """按题型统计练习与得分。"""
    query = (
        select(
            Review.question_type_snapshot,
            func.count(Review.id),
            func.avg(Review.score),
            func.max(Review.score),
        )
        .where(
            Review.user_id == user_id,
            Review.question_type_snapshot.isnot(None),
            Review.question_type_snapshot != "",
        )
        .group_by(Review.question_type_snapshot)
    )

    if date_from is not None:
        query = query.where(Review.created_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.where(Review.created_at <= datetime.combine(date_to, time.max))

    rows = db.execute(query.order_by(func.count(Review.id).desc())).all()

    results = []
    for row in rows:
        question_type = row[0]
        count = row[1]
        avg_score = round(float(row[2]), 1) if row[2] is not None else None
        best_score = int(row[3]) if row[3] is not None else None

        # 获取该题型最近一次分数
        latest_score = db.scalar(
            select(Review.score)
            .where(
                Review.user_id == user_id,
                Review.question_type_snapshot == question_type,
                Review.score.isnot(None),
            )
            .order_by(Review.created_at.desc(), Review.id.desc())
            .limit(1)
        )

        results.append({
            "question_type": question_type,
            "count": count,
            "avg_score": avg_score,
            "best_score": best_score,
            "latest_score": int(latest_score) if latest_score is not None else None,
        })

    return results


def get_random_question(
    db: Session,
    user_id: int,
    *,
    question_type: str | None = None,
    tag: str | None = None,
    source: str | None = None,
) -> Question | None:
    """随机返回一道题目。"""
    query = select(Question).where(Question.user_id == user_id)

    if question_type:
        query = query.where(Question.question_type == question_type)
    if tag:
        query = query.where(Question.tags.ilike(f"%{tag.strip()}%"))
    if source:
        query = query.where(Question.source == source)

    query = query.order_by(func.random()).limit(1)
    return db.scalars(query).first()


def get_recommended_questions(
    db: Session,
    user_id: int,
    *,
    limit: int = 5,
) -> list[dict]:
    """基于薄弱题型推荐题目（优先推荐用户未练习过或得分低的题型）。"""
    # 获取薄弱题型
    weak_types = get_weak_question_types(db, user_id, limit=5)

    # 获取用户已练习过的题目 ID
    practiced_question_ids = set(
        db.scalars(
            select(distinct(PracticeRecord.question_id)).where(PracticeRecord.user_id == user_id)
        ).all()
    )

    results: list[dict] = []

    # 优先推荐薄弱题型中未练习的题目
    if weak_types:
        query = (
            select(Question)
            .where(
                Question.user_id == user_id,
                Question.question_type.in_(weak_types),
            )
            .order_by(func.random())
            .limit(limit)
        )
        questions = db.scalars(query).all()
        for q in questions:
            practiced = q.id in practiced_question_ids
            reason = f"你在「{q.question_type}」题型上得分较低，{'建议再练一次' if practiced else '建议尝试这道题'}"
            results.append({
                "question_id": q.id,
                "title": q.title,
                "question_type": q.question_type,
                "tags": [t.strip() for t in (q.tags or "").split(",") if t.strip()],
                "reason": reason,
            })

    # 如果不够，补充未练习过的题目
    if len(results) < limit:
        remaining = limit - len(results)
        existing_ids = {item["question_id"] for item in results}
        query = (
            select(Question)
            .where(
                Question.user_id == user_id,
                Question.id.notin_(practiced_question_ids | existing_ids) if (practiced_question_ids | existing_ids) else True,
            )
            .order_by(func.random())
            .limit(remaining)
        )
        questions = db.scalars(query).all()
        for q in questions:
            results.append({
                "question_id": q.id,
                "title": q.title,
                "question_type": q.question_type,
                "tags": [t.strip() for t in (q.tags or "").split(",") if t.strip()],
                "reason": "你还没有练习过这道题",
            })

    return results[:limit]


def get_score_trend(
    db: Session,
    user_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    granularity: str = "day",
) -> list[dict]:
    """获取得分趋势（按天/周聚合）。"""
    query = select(
        func.date(Review.created_at).label("review_date"),
        func.count(Review.id).label("count"),
        func.avg(Review.score).label("avg_score"),
    ).where(
        Review.user_id == user_id,
        Review.score.isnot(None),
    ).group_by(func.date(Review.created_at)).order_by(func.date(Review.created_at).asc())

    if date_from is not None:
        query = query.where(Review.created_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.where(Review.created_at <= datetime.combine(date_to, time.max))

    rows = db.execute(query).all()

    results = []
    for row in rows:
        review_date = row[0]
        if isinstance(review_date, date):
            date_str = review_date.isoformat()
        else:
            date_str = str(review_date)
        results.append({
            "date": date_str,
            "count": row[1],
            "avg_score": round(float(row[2]), 1) if row[2] is not None else None,
        })

    return results


def get_latest_answer_for_question(
    db: Session,
    user_id: int,
    question_id: int,
) -> Answer | None:
    """获取用户在某题上的最近一次答案。"""
    return db.scalars(
        select(Answer)
        .where(Answer.user_id == user_id, Answer.question_id == question_id)
        .order_by(Answer.version_no.desc(), Answer.id.desc())
        .limit(1)
    ).first()


def get_review_for_compare(db: Session, review_id: int) -> Review | None:
    """获取批改记录用于对比。"""
    return db.get(Review, review_id)
