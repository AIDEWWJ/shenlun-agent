from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import api_error


def _validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for item in exc.errors():
        details.append(
            {
                "loc": item.get("loc"),
                "msg": item.get("msg"),
                "type": item.get("type"),
            }
        )
    return details


def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    payload = api_error(
        message=str(exc.detail),
        code=str(exc.status_code),
        details=None,
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = api_error(
        message="请求参数校验失败",
        code="VALIDATION_ERROR",
        details=_validation_details(exc),
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


def unexpected_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    payload = api_error(
        message="服务器内部错误",
        code="INTERNAL_SERVER_ERROR",
        details=None,
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
