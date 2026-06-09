from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.modules.question.models import Question

SQLITE_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class Answer(Base):
	__tablename__ = "answers"
	__table_args__ = (
		UniqueConstraint("question_id", "user_id", "version_no", name="uk_answers_question_user_version"),
	)

	id = Column(Integer, primary_key=True, index=True)
	question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	paper_id = Column(SQLITE_BIGINT, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True)
	content = Column(Text, nullable=False)
	version_no = Column(Integer, nullable=False, default=1)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	question = relationship("Question", back_populates="answers")
	user = relationship("User", back_populates="answers")
	paper = relationship("Paper")
	reviews = relationship("Review", back_populates="answer", cascade="all, delete-orphan")
	practice_records = relationship(
		"PracticeRecord",
		back_populates="answer",
		cascade="all, delete-orphan",
	)


class PracticeRecord(Base):
	__tablename__ = "practice_records"
	__table_args__ = (
		UniqueConstraint("answer_id", name="uk_practice_records_answer_id"),
		Index("idx_practice_records_user_id_id", "user_id", "id"),
		Index("idx_practice_records_user_status_id", "user_id", "status", "id"),
		Index("idx_practice_records_user_question_id", "user_id", "question_id", "id"),
		Index("idx_practice_records_review_id", "review_id"),
	)

	id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	paper_id = Column(SQLITE_BIGINT, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True)
	question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
	answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
	review_id = Column(SQLITE_BIGINT, ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True)
	status = Column(String(32), nullable=False, default="finished")
	is_favorite = Column(Boolean, nullable=False, default=False)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	user = relationship("User", back_populates="practice_records")
	paper = relationship("Paper")
	question = relationship("Question", back_populates="practice_records")
	answer = relationship("Answer", back_populates="practice_records")
	review = relationship("Review", back_populates="practice_records")


class PaperPracticeSession(Base):
	__tablename__ = "paper_practice_sessions"
	__table_args__ = (
		UniqueConstraint("user_id", "paper_id", name="uk_paper_practice_user_paper"),
		Index("idx_paper_practice_status", "user_id", "status"),
	)

	id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
	user_id = Column(SQLITE_BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	paper_id = Column(SQLITE_BIGINT, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
	answers_json = Column(Text, nullable=False, default="{}")
	current_index = Column(Integer, nullable=False, default=0)
	timer_seconds = Column(Integer, nullable=False, default=0)
	status = Column(String(32), nullable=False, default="drafting")
	started_at = Column(DateTime, server_default=func.now(), nullable=False)
	updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

	user = relationship("User")
	paper = relationship("Paper")


__all__ = ["Answer", "PracticeRecord", "PaperPracticeSession", "Question"]
