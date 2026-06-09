from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base

SQLITE_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class Question(Base):
	__tablename__ = "questions"
	__table_args__ = (
		Index("idx_questions_user_id_id", "user_id", "id"),
		Index("idx_questions_question_type_id", "question_type", "id"),
		Index("idx_questions_source_id", "source", "id"),
		Index("idx_questions_scope_id", "scope", "id"),
	)

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=True)
	scope = Column(String(16), nullable=False, default="user")
	title = Column(String(255), nullable=False)
	content = Column(Text, nullable=False)
	material = Column(Text, nullable=True)
	material_refs = Column(String(64), nullable=True)
	requirement = Column(Text, nullable=True)
	sort_order = Column(Integer, nullable=True)
	category = Column(String(32), nullable=True)
	year = Column(Integer, nullable=True)
	region = Column(String(64), nullable=True)
	question_type = Column(String(64), nullable=True)
	difficulty = Column(String(32), nullable=True)
	theme = Column(String(64), nullable=True)
	suggested_minutes = Column(Integer, nullable=True)
	tags = Column(String(255), nullable=True)
	source = Column(String(255), nullable=True)
	cover_note = Column(String(255), nullable=True)
	intro = Column(Text, nullable=True)
	overview = Column(Text, nullable=True)
	tasks_json = Column(Text, nullable=True)
	instructions_json = Column(Text, nullable=True)
	notices_json = Column(Text, nullable=True)
	materials_json = Column(Text, nullable=True)
	answer_sections_json = Column(Text, nullable=True)
	reference_answer = Column(Text, nullable=True)
	optimized_example = Column(Text, nullable=True)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	user = relationship("User", back_populates="questions")
	paper = relationship("Paper", back_populates="questions")
	answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
	practice_records = relationship(
		"PracticeRecord",
		back_populates="question",
		cascade="all, delete-orphan",
	)


class QuestionFavorite(Base):
	"""用户题目收藏。"""

	__tablename__ = "question_favorites"
	__table_args__ = (
		UniqueConstraint("user_id", "question_id", name="uk_question_favorites_user_question"),
		Index("idx_question_favorites_user_id", "user_id"),
	)

	id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
	user_id = Column(SQLITE_BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	question_id = Column(SQLITE_BIGINT, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	user = relationship("User")
	question = relationship("Question")


__all__ = ["Question", "QuestionFavorite"]
