from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PaperCreate(BaseModel):
    title: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=32)
    region: Optional[str] = Field(None, max_length=64)
    difficulty: Optional[str] = Field(None, max_length=32)
    year: Optional[int] = None
    source_url: Optional[str] = Field(None, max_length=512)
    scope: str = Field("system", max_length=16)


class PaperRead(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    region: Optional[str] = None
    difficulty: Optional[str] = None
    year: Optional[int] = None
    source_url: Optional[str] = None
    scope: str
    question_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaperMaterialItem(BaseModel):
    """试卷中的材料。"""
    material_num: int
    content: str
    sort_order: Optional[int] = None


class PaperQuestionItem(BaseModel):
    """试卷中的单道小题（用于导入）。"""
    material_refs: Optional[str] = None
    requirement: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    sort_order: Optional[int] = None


class PaperImportRequest(BaseModel):
    """批量导入试卷+材料+小题的请求体。"""
    title: str
    category: Optional[str] = None
    region: Optional[str] = None
    difficulty: Optional[str] = None
    year: Optional[int] = None
    source_url: Optional[str] = None
    scope: str = "system"
    materials: List[PaperMaterialItem] = []
    questions: List[PaperQuestionItem] = []


class PaperMaterialRead(BaseModel):
    """试卷详情中的材料。"""
    id: int
    material_num: int
    content: str
    sort_order: Optional[int] = None

    class Config:
        from_attributes = True


class PaperQuestionRead(BaseModel):
    """试卷详情中的小题。"""
    id: int
    material_refs: Optional[str] = None
    requirement: Optional[str] = None
    reference_answer: Optional[str] = None
    difficulty: Optional[str] = None
    sort_order: Optional[int] = None
    question_type: Optional[str] = None

    class Config:
        from_attributes = True


class PaperDetailRead(PaperRead):
    """试卷详情，含材料和小题列表。"""
    materials: List[PaperMaterialRead] = []
    questions: List[PaperQuestionRead] = []


__all__ = [
    "PaperCreate",
    "PaperRead",
    "PaperMaterialItem",
    "PaperImportRequest",
    "PaperMaterialRead",
    "PaperQuestionRead",
    "PaperDetailRead",
]
