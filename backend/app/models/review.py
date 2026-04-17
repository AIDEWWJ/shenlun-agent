from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=True)
    strengths = Column(Text, nullable=True)
    issues = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    answer = relationship("Answer", back_populates="reviews")
    practice_records = relationship("PracticeRecord", back_populates="review")
