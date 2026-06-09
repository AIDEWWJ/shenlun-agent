"""错题本与学习计划数据模型。"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base

SQLITE_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class ErrorNotebookEntry(Base):
    """错题本条目。"""

    __tablename__ = "error_notebook_entries"
    __table_args__ = (
        Index("idx_error_notebook_user_id_status", "user_id", "status"),
    )

    id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
    user_id = Column(SQLITE_BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(SQLITE_BIGINT, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    review_id = Column(SQLITE_BIGINT, ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True)
    error_type = Column(String(64), nullable=False, default="low_score")
    error_summary = Column(Text, nullable=True)
    missing_points = Column(Text, nullable=True)
    weak_dimensions = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="unresolved")
    resolve_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User")
    question = relationship("Question")
    review = relationship("Review")


class StudyPlan(Base):
    """学习计划。"""

    __tablename__ = "study_plans"
    __table_args__ = (
        Index("idx_study_plans_user_id_status", "user_id", "status"),
    )

    id = Column(SQLITE_BIGINT, primary_key=True, index=True, autoincrement=True)
    user_id = Column(SQLITE_BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    plan_json = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="active")
    generated_by = Column(String(64), nullable=False, default="ai")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")


__all__ = ["ErrorNotebookEntry", "StudyPlan"]
