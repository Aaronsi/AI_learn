from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import settings


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class AppError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, details: dict | None = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
    request: Request | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )
    # 确保异常响应也包含 CORS 头
    if request:
        origin = request.headers.get("origin")
        if origin:
            # 允许的源列表（与 main.py 中的配置保持一致）
            default_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
            ]
            allowed_origins = (
                settings.allowed_origins
                if settings.allowed_origins
                else default_origins
            )
            if origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
    return response


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:  # type: ignore[override]
    return error_response(
        exc.status_code, exc.code, exc.message, exc.details, request=request
    )
