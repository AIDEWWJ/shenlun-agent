from typing import Any

from fastapi.encoders import jsonable_encoder


def api_success(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": jsonable_encoder(data),
        "error": None,
    }


def api_error(message: str, code: str | None = None, details: Any = None) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "details": jsonable_encoder(details),
        },
    }
