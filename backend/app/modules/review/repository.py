from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.review.models import Review, ReviewQAMessage, ReviewStep


def get_review(db: Session, review_id: int) -> Review | None:
	return db.get(Review, review_id)


def get_review_qa_message(db: Session, message_id: int) -> ReviewQAMessage | None:
	return db.get(ReviewQAMessage, message_id)


def get_review_by_answer_id(db: Session, answer_id: int) -> Review | None:
	return db.scalars(select(Review).where(Review.answer_id == answer_id)).first()


def list_reviews(
	db: Session,
	*,
	user_id: int | None = None,
	question_id: int | None = None,
	question_type: str | None = None,
	page: int = 1,
	page_size: int = 20,
) -> tuple[list[Review], int]:
	query = select(Review)
	count_query = select(func.count(Review.id))
	if user_id is not None:
		query = query.where(Review.user_id == user_id)
		count_query = count_query.where(Review.user_id == user_id)
	if question_id is not None:
		query = query.where(Review.question_id == question_id)
		count_query = count_query.where(Review.question_id == question_id)
	if question_type:
		query = query.where(Review.question_type_snapshot == question_type)
		count_query = count_query.where(Review.question_type_snapshot == question_type)
	total = db.scalar(count_query) or 0
	items = db.scalars(query.order_by(Review.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
	return items, total


def list_review_steps(db: Session, review_id: int) -> list[ReviewStep]:
	return db.scalars(
		select(ReviewStep)
		.where(ReviewStep.review_id == review_id)
		.order_by(ReviewStep.order_no.asc(), ReviewStep.id.asc())
	).all()


def create_review_qa_message(db: Session, message: ReviewQAMessage) -> ReviewQAMessage:
	db.add(message)
	db.flush()
	return message


def list_review_qa_messages(
	db: Session,
	*,
	review_id: int,
	user_id: int | None = None,
	conversation_id: str | None = None,
	page: int = 1,
	page_size: int = 20,
) -> tuple[list[ReviewQAMessage], int]:
	query = select(ReviewQAMessage).where(ReviewQAMessage.review_id == review_id)
	count_query = select(func.count(ReviewQAMessage.id)).where(ReviewQAMessage.review_id == review_id)
	if user_id is not None:
		query = query.where(ReviewQAMessage.user_id == user_id)
		count_query = count_query.where(ReviewQAMessage.user_id == user_id)
	if conversation_id is not None:
		query = query.where(ReviewQAMessage.conversation_id == conversation_id)
		count_query = count_query.where(ReviewQAMessage.conversation_id == conversation_id)
	total = db.scalar(count_query) or 0
	items = db.scalars(
		query.order_by(ReviewQAMessage.round_no.asc(), ReviewQAMessage.id.asc()).offset((page - 1) * page_size).limit(page_size)
	).all()
	return items, total
