import logging
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .errors import AppError, app_error_handler, error_response
from .logger import json_log, setup_logging
from .routes import health, tags, tickets

setup_logging()
logger = logging.getLogger(__name__)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > settings.max_request_size:
                    return error_response(
                        status_code=413,
                        code="request_too_large",
                        message="请求体超过限制",
                        details={"max_bytes": settings.max_request_size},
                        request=request,
                    )
            except ValueError:
                pass
        response = await call_next(request)
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="Project Alpha API", version="0.1.0")

    # CORS 配置：如果配置了允许的源，使用配置；否则允许所有源（仅开发环境）
    # 确保包含常见的前端开发端口
    default_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    cors_origins = (
        settings.allowed_origins if settings.allowed_origins else default_origins
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(BodySizeLimitMiddleware)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[override]
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration = (time.perf_counter() - start) * 1000
            json_log(
                "request_completed",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": round(duration, 2),
                },
            )
            return response
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            json_log(
                "request_failed",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(exc),
                    "duration_ms": round(duration, 2),
                },
                level=logging.ERROR,
            )
            raise

    app.include_router(health.router)
    app.include_router(tags.router)
    app.include_router(tickets.router)

    app.add_exception_handler(AppError, app_error_handler)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:  # type: ignore[override]
        return error_response(
            status_code=exc.status_code,
            code="http_error",
            message=str(exc.detail or "请求失败"),
            request=request,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:  # type: ignore[override]
        return error_response(
            status_code=422,
            code="validation_error",
            message="请求参数校验失败",
            details={"errors": exc.errors()},
            request=request,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:  # type: ignore[override]
        logger.exception("Unhandled error: %s", exc)
        return error_response(
            status_code=500,
            code="internal_error",
            message="服务器内部错误",
            request=request,
        )

    return app


app = create_app()
