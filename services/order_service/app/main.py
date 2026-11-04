import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Tuple

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger, setup_logging
from app.core.telemetry import setup_telemetry, shutdown_telemetry
from app.db.base import Base
from app.db.session import engine


def get_current_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    span = trace.get_current_span()
    span_ctx = span.get_span_context() if span else None
    if span_ctx and span_ctx.is_valid:
        return f"{span_ctx.trace_id:032x}", f"{span_ctx.span_id:016x}"
    return None, None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("Initializing %s in %s mode...", settings.PROJECT_NAME, settings.ENVIRONMENT)

    setup_telemetry(app=app, engine=engine)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema validated/created successfully for %s", settings.SERVICE_NAME)
    except Exception as exc:
        logger.error("Failed database connectivity on startup: %s", str(exc), exc_info=True)

    yield

    logger.info("Initiating graceful shutdown...")
    shutdown_telemetry()
    await engine.dispose()
    logger.info("Application shutdown completed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise-grade production-ready Order microservice with OpenTelemetry distributed tracing and saga orchestration.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


@app.middleware("http")
async def correlation_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = (time.perf_counter() - start_time) * 1000
    trace_id, span_id = get_current_trace_ids()

    response.headers["X-Request-ID"] = request_id
    if trace_id:
        response.headers["X-Trace-ID"] = trace_id
    if span_id:
        response.headers["X-Span-ID"] = span_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    trace_id, span_id = get_current_trace_ids()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "meta": {
                "request_id": request.headers.get("X-Request-ID", "unknown"),
                "trace_id": trace_id,
                "span_id": span_id,
                "path": request.url.path,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id, span_id = get_current_trace_ids()
    errors = [
        {"field": " -> ".join(str(loc) for loc in err.get("loc", [])), "message": err.get("msg")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "status_code": 422,
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed.",
            "details": errors,
            "meta": {
                "request_id": request.headers.get("X-Request-ID", "unknown"),
                "trace_id": trace_id,
                "span_id": span_id,
                "path": request.url.path,
            },
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    trace_id, span_id = get_current_trace_ids()
    logger.error("Database integrity error: %s", str(exc.orig), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "status_code": 409,
            "error_code": "DATA_INTEGRITY_CONFLICT",
            "message": "Database constraint violation occurred.",
            "meta": {
                "request_id": request.headers.get("X-Request-ID", "unknown"),
                "trace_id": trace_id,
                "span_id": span_id,
                "path": request.url.path,
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = request.headers.get("X-Request-ID", "unknown")
    trace_id, span_id = get_current_trace_ids()
    logger.exception("Unhandled exception [request_id=%s, trace_id=%s]: %s", req_id, trace_id, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please contact system support.",
            "meta": {
                "request_id": req_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "path": request.url.path,
            },
        },
    )


@app.get("/health", tags=["System"])
async def health_check():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": settings.SERVICE_NAME,
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "tracing": "enabled" if settings.OTEL_ENABLED else "disabled",
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "docs": f"{settings.API_V1_STR}/docs",
        "version": "1.0.0",
    }


app.include_router(api_v1_router, prefix=settings.API_V1_STR)

