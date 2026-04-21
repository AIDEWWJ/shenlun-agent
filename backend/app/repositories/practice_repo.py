"""练习数据访问层。

这里放题目、答案、批改记录、练习记录等数据库访问逻辑。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Answer, PracticeRecord, Question, Review


def get_question(db: Session, question_id: int) -> Question | None:
	return db.get(Question, question_id)


def get_answer(db: Session, answer_id: int) -> Answer | None:
	return db.get(Answer, answer_id)


def get_review_by_answer_id(db: Session, answer_id: int) -> Review | None:
	return db.scalars(select(Review).where(Review.answer_id == answer_id).order_by(Review.id.desc())).first()


def create_review(db: Session, *, answer_id: int, score: int | None, strengths: str | None, issues: str | None, suggestions: str | None, summary: str | None) -> Review:
	review = Review(
		answer_id=answer_id,
		score=score,
		strengths=strengths,
		issues=issues,
		suggestions=suggestions,
		summary=summary,
	)
	db.add(review)
	db.flush()
	return review


def create_practice_record(
	db: Session,
	*,
	user_id: int,
	question_id: int,
	answer_id: int,
	review_id: int | None = None,
	status: str = "finished",
) -> PracticeRecord:
	record = PracticeRecord(
		user_id=user_id,
		question_id=question_id,
		answer_id=answer_id,
		review_id=review_id,
		status=status,
	)
	db.add(record)
	db.flush()
	return record
"""练习数据访问层。

这里放题目、答案、批改记录、练习记录等数据库访问逻辑。
"""
