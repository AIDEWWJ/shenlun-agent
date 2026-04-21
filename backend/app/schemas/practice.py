from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreateRequest(BaseModel):
	"""答案批改请求。"""

	question_id: int = Field(ge=1)
	answer_id: int = Field(ge=1)
	reference_points: list[str] = Field(default_factory=list)
	use_llm: bool = True
	question_title: Optional[str] = Field(default=None, max_length=255)
	question_content: Optional[str] = None
	question_type: Optional[str] = Field(default=None, max_length=64)
	answer_content: Optional[str] = None