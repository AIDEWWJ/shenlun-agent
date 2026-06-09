from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base

SQLITE_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class Review(Base):
	__tablename__ = "reviews"
	__table_args__ = (
		UniqueConstraint("answer_id", name="uk_reviews_answer_id"),
		Index("idx_reviews_user_id_id", "user_id", "id"),
		Index("idx_reviews_question_id_id", "question_id", "id"),
	)

	id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
	answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
	question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	paper_id = Column(SQLITE_BIGINT, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True)
	question_title_snapshot = Column(String(255), nullable=False)
	question_type_snapshot = Column(String(64), nullable=True)
	question_content_snapshot = Column(Text, nullable=False)
	answer_content_snapshot = Column(Text, nullable=False)
	reference_points_json = Column(Text, nullable=False)
	question_analysis_json = Column(Text, nullable=False)
	reference_point_analysis_json = Column(Text, nullable=False)
	user_point_analysis_json = Column(Text, nullable=False)
	comparison_json = Column(Text, nullable=False)
	structure_analysis_json = Column(Text, nullable=False)
	language_analysis_json = Column(Text, nullable=False)
	rule_analysis_json = Column(Text, nullable=False)
	score_breakdown_json = Column(Text, nullable=False)
	report_json = Column(Text, nullable=False)
	model_provider = Column(String(64), nullable=True)
	model_name = Column(String(128), nullable=True)
	score = Column(Integer, nullable=True)
	strengths = Column(Text, nullable=True)
	issues = Column(Text, nullable=True)
	suggestions = Column(Text, nullable=True)
	summary = Column(Text, nullable=True)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	answer = relationship("Answer", back_populates="reviews")
	question = relationship("Question")
	user = relationship("User")
	practice_records = relationship("PracticeRecord", back_populates="review")
	steps = relationship("ReviewStep", back_populates="review", cascade="all, delete-orphan")


class ReviewStep(Base):
	__tablename__ = "review_steps"
	__table_args__ = (
		Index("idx_review_steps_review_order_id", "review_id", "order_no", "id"),
	)

	id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
	review_id = Column(SQLITE_BIGINT, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
	step_key = Column(String(64), nullable=False)
	step_name = Column(String(128), nullable=False)
	order_no = Column(Integer, nullable=False)
	status = Column(String(32), nullable=False, default="success")
	critical = Column(Boolean, nullable=False, default=True)
	attempts = Column(Integer, nullable=False, default=1)
	error = Column(Text, nullable=True)
	input_json = Column(Text, nullable=False)
	output_json = Column(Text, nullable=False)
	note = Column(Text, nullable=True)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	review = relationship("Review", back_populates="steps")


class ReviewQAMessage(Base):
	__tablename__ = "review_qa_messages"
	__table_args__ = (
		Index("idx_review_qa_messages_review_conversation_round", "review_id", "conversation_id", "round_no"),
		Index("idx_review_qa_messages_user_id_id", "user_id", "id"),
	)

	id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
	review_id = Column(SQLITE_BIGINT, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	conversation_id = Column(String(64), nullable=False)
	parent_message_id = Column(SQLITE_BIGINT, ForeignKey("review_qa_messages.id", ondelete="SET NULL"), nullable=True)
	round_no = Column(Integer, nullable=False, default=1)
	question_text = Column(Text, nullable=False)
	question_category = Column(String(64), nullable=False)
	answer_text = Column(Text, nullable=False)
	evidence_refs_json = Column(Text, nullable=False)
	used_llm = Column(Boolean, nullable=False, default=False)
	created_at = Column(DateTime, server_default=func.now(), nullable=False)

	review = relationship("Review")
	user = relationship("User")
	parent_message = relationship("ReviewQAMessage", remote_side=[id])


__all__ = ["Review", "ReviewStep", "ReviewQAMessage"]
