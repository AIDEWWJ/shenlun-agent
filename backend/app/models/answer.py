from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    version_no = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    question = relationship("Question", back_populates="answers")
    user = relationship("User", back_populates="answers")
    reviews = relationship("Review", back_populates="answer", cascade="all, delete-orphan")
    practice_records = relationship(
        "PracticeRecord",
        back_populates="answer",
        cascade="all, delete-orphan",
    )
