from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
	code: str | None = None
	details: Any = None


class ApiResponse(BaseModel):
	success: bool = True
	message: str = Field(default="success")
	data: Any = None
	error: ErrorDetail | None = None


__all__ = ["ApiResponse", "ErrorDetail"]
