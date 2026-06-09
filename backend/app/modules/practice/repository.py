from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.practice.models import Answer, PaperPracticeSession, PracticeRecord, Question
from app.modules.review.models import Review, ReviewStep


def get_question(db: Session, question_id: int) -> Question | None:
	return db.get(Question, question_id)


def get_answer(db: Session, answer_id: int) -> Answer | None:
	return db.get(Answer, answer_id)


def list_answers(
	db: Session,
	*,
	user_id: int | None = None,
	question_id: int | None = None,
	page: int = 1,
	page_size: int = 20,
) -> tuple[list[Answer], int]:
	query = select(Answer)
	count_query = select(func.count(Answer.id))

	if user_id is not None:
		query = query.where(Answer.user_id == user_id)
		count_query = count_query.where(Answer.user_id == user_id)
	if question_id is not None:
		query = query.where(Answer.question_id == question_id)
		count_query = count_query.where(Answer.question_id == question_id)

	total = db.scalar(count_query) or 0
	items = db.scalars(
		query.order_by(Answer.version_no.desc(), Answer.id.desc()).offset((page - 1) * page_size).limit(page_size)
	).all()
	return items, total


def get_latest_answer_version_no(db: Session, *, user_id: int, question_id: int) -> int:
	value = db.scalar(
		select(func.max(Answer.version_no)).where(Answer.user_id == user_id, Answer.question_id == question_id)
	)
	return int(value or 0)


def create_answer(db: Session, answer: Answer) -> Answer:
	db.add(answer)
	db.flush()
	return answer


def update_answer(db: Session, answer: Answer, *, content: str | None = None) -> Answer:
	if content is not None:
		answer.content = content
	db.flush()
	return answer


def get_review_by_answer_id(db: Session, answer_id: int) -> Review | None:
	return db.scalars(select(Review).where(Review.answer_id == answer_id)).first()


def create_review(db: Session, *, review_data: dict) -> Review:
	review = Review(**review_data)
	db.add(review)
	db.flush()
	return review


def update_review(db: Session, review: Review, review_data: dict) -> Review:
	for key, value in review_data.items():
		setattr(review, key, value)
	db.flush()
	return review


def delete_review_steps(db: Session, review_id: int) -> None:
	db.execute(delete(ReviewStep).where(ReviewStep.review_id == review_id))


def create_review_step(db: Session, step: ReviewStep) -> ReviewStep:
	db.add(step)
	db.flush()
	return step


def create_practice_record(
	db: Session,
	*,
	user_id: int,
	paper_id: int | None = None,
	question_id: int,
	answer_id: int,
	review_id: int | None = None,
	status: str = "finished",
) -> PracticeRecord:
	record = PracticeRecord(
		user_id=user_id,
		paper_id=paper_id,
		question_id=question_id,
		answer_id=answer_id,
		review_id=review_id,
		status=status,
	)
	db.add(record)
	db.flush()
	return record


# Deprecated: practice_sessions table removed, stub functions for backward compatibility
def get_current_practice_session_by_question(db, *, user_id, question_id):
	return None

def get_practice_session(db, session_id):
	return None

def create_practice_session(db, session):
	return session

def update_practice_session(db, session, **kwargs):
	return session



def get_practice_record(db: Session, record_id: int) -> PracticeRecord | None:
	return db.get(PracticeRecord, record_id)


def get_practice_record_by_answer_id(db: Session, answer_id: int) -> PracticeRecord | None:
	return db.scalars(select(PracticeRecord).where(PracticeRecord.answer_id == answer_id)).first()


def get_latest_review_for_question(db: Session, *, user_id: int, question_id: int) -> Review | None:
	return db.scalars(
		select(Review)
		.where(Review.user_id == user_id, Review.question_id == question_id)
		.order_by(Review.created_at.desc(), Review.id.desc())
	).first()


def update_practice_record(
	db: Session,
	record: PracticeRecord,
	*,
	review_id: int | None = None,
	status: str | None = None,
	is_favorite: bool | None = None,
) -> PracticeRecord:
	if review_id is not None:
		record.review_id = review_id
	if status is not None:
		record.status = status
	if is_favorite is not None:
		record.is_favorite = is_favorite
	db.flush()
	return record


def list_practice_records(
	db: Session,
	*,
	user_id: int | None = None,
	paper_id: int | None = None,
	question_id: int | None = None,
	question_type: str | None = None,
	answer_version_no: int | None = None,
	status: str | None = None,
	review_id: int | None = None,
	score_min: int | None = None,
	score_max: int | None = None,
	model_provider: str | None = None,
	model_name: str | None = None,
	is_favorite: bool | None = None,
	created_from: datetime | None = None,
	created_to: datetime | None = None,
	page: int = 1,
	page_size: int = 20,
) -> tuple[list[PracticeRecord], int]:
	query = select(PracticeRecord)
	count_query = select(func.count(PracticeRecord.id))
	joined_question = False
	joined_answer = False
	joined_review = False

	if user_id is not None:
		query = query.where(PracticeRecord.user_id == user_id)
		count_query = count_query.where(PracticeRecord.user_id == user_id)
	if paper_id is not None:
		query = query.where(PracticeRecord.paper_id == paper_id)
		count_query = count_query.where(PracticeRecord.paper_id == paper_id)
	if question_id is not None:
		query = query.where(PracticeRecord.question_id == question_id)
		count_query = count_query.where(PracticeRecord.question_id == question_id)
	if question_type:
		if not joined_question:
			query = query.join(Question, PracticeRecord.question_id == Question.id)
			count_query = count_query.join(Question, PracticeRecord.question_id == Question.id)
			joined_question = True
		query = query.where(Question.question_type == question_type)
		count_query = count_query.where(Question.question_type == question_type)
	if answer_version_no is not None:
		if not joined_answer:
			query = query.join(Answer, PracticeRecord.answer_id == Answer.id)
			count_query = count_query.join(Answer, PracticeRecord.answer_id == Answer.id)
			joined_answer = True
		query = query.where(Answer.version_no == answer_version_no)
		count_query = count_query.where(Answer.version_no == answer_version_no)
	if status:
		query = query.where(PracticeRecord.status == status)
		count_query = count_query.where(PracticeRecord.status == status)
	if review_id is not None:
		query = query.where(PracticeRecord.review_id == review_id)
		count_query = count_query.where(PracticeRecord.review_id == review_id)
	if score_min is not None or score_max is not None or model_provider or model_name:
		if not joined_review:
			query = query.join(Review, PracticeRecord.review_id == Review.id)
			count_query = count_query.join(Review, PracticeRecord.review_id == Review.id)
			joined_review = True
		if score_min is not None:
			query = query.where(Review.score >= score_min)
			count_query = count_query.where(Review.score >= score_min)
		if score_max is not None:
			query = query.where(Review.score <= score_max)
			count_query = count_query.where(Review.score <= score_max)
	if model_provider:
		query = query.where(Review.model_provider == model_provider)
		count_query = count_query.where(Review.model_provider == model_provider)
	if model_name:
		query = query.where(Review.model_name == model_name)
		count_query = count_query.where(Review.model_name == model_name)
	if is_favorite is not None:
		query = query.where(PracticeRecord.is_favorite == is_favorite)
		count_query = count_query.where(PracticeRecord.is_favorite == is_favorite)
	if created_from is not None:
		query = query.where(PracticeRecord.created_at >= created_from)
		count_query = count_query.where(PracticeRecord.created_at >= created_from)
	if created_to is not None:
		query = query.where(PracticeRecord.created_at <= created_to)
		count_query = count_query.where(PracticeRecord.created_at <= created_to)

	total = db.scalar(count_query) or 0
	items = db.scalars(
		query.order_by(PracticeRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)
	).all()
	return items, total


# ========== 整套试卷练习会话 ==========

def get_paper_practice_session(db: Session, user_id: int, paper_id: int):
	"""获取用户在某套试卷上的练习会话。"""
	return db.scalars(
		select(PaperPracticeSession).where(
			PaperPracticeSession.user_id == user_id,
			PaperPracticeSession.paper_id == paper_id,
		)
	).first()


def upsert_paper_practice_session(
	db: Session,
	user_id: int,
	paper_id: int,
	answers_json: str,
	current_index: int,
	timer_seconds: int,
	status: str = "drafting",
):
	"""保存或更新试卷练习会话。"""
	session = get_paper_practice_session(db, user_id, paper_id)
	if session:
		session.answers_json = answers_json
		session.current_index = current_index
		session.timer_seconds = timer_seconds
		session.status = status
	else:
		session = PaperPracticeSession(
			user_id=user_id,
			paper_id=paper_id,
			answers_json=answers_json,
			current_index=current_index,
			timer_seconds=timer_seconds,
			status=status,
		)
		db.add(session)
	db.flush()
	return session


def delete_paper_practice_session(db: Session, user_id: int, paper_id: int):
	"""删除试卷练习会话。"""
	session = get_paper_practice_session(db, user_id, paper_id)
	if session:
		db.delete(session)
		db.flush()
