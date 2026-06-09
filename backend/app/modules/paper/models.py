from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base

SQLITE_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class Paper(Base):
    __tablename__ = "papers"
    __table_args__ = (
        Index("idx_papers_scope_id", "scope", "id"),
        Index("idx_papers_user_id", "user_id", "id"),
        Index("idx_papers_region_year", "region", "year"),
    )

    id = Column(SQLITE_BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(SQLITE_BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String(16), nullable=False, default="system")
    title = Column(String(255), nullable=False)
    category = Column(String(32), nullable=True)
    region = Column(String(64), nullable=True)
    difficulty = Column(String(32), nullable=True)
    year = Column(Integer, nullable=True)
    source_url = Column(String(512), nullable=True)
    question_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    questions = relationship("Question", back_populates="paper", cascade="all, delete-orphan", order_by="Question.sort_order")
    materials = relationship("PaperMaterial", back_populates="paper", cascade="all, delete-orphan", order_by="PaperMaterial.material_num")


class PaperMaterial(Base):
    __tablename__ = "paper_materials"
    __table_args__ = (
        Index("idx_paper_materials_paper_id", "paper_id", "material_num"),
    )

    id = Column(SQLITE_BIGINT, primary_key=True, autoincrement=True)
    paper_id = Column(SQLITE_BIGINT, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    material_num = Column(Integer, nullable=False, comment="材料编号")
    content = Column(Text, nullable=False, comment="材料正文")
    sort_order = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    paper = relationship("Paper", back_populates="materials")


__all__ = ["Paper", "PaperMaterial"]
