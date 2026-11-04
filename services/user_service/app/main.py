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
from app.db.session import engine


def get_current_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    """Helper to retrieve active OpenTelemetry trace_id and span_id."""
    span = trace.get_current_span()
    span_ctx = span.get_span_context() if span else None
    if span_ctx and span_ctx.is_valid:
        return f"{span_ctx.trace_id:032x}", f"{span_ctx.span_id:016x}"
    return None, None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing logging, OpenTelemetry, connection pool, and resources."""
    setup_logging()
    logger.info("Initializing %s in %s mode...", settings.PROJECT_NAME, settings.ENVIRONMENT)

    # Initialize OpenTelemetry distributed tracing and instrumentations
    setup_telemetry(app=app, engine=engine)

    # Verify database connectivity
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to MySQL database: %s", settings.MYSQL_DB)
    except Exception as exc:
        logger.error("Failed to connect to MySQL database on startup: %s", str(exc), exc_info=True)

    yield

    # Clean shutdown: Flush traces and close connection pool
    logger.info("Initiating graceful shutdown...")
    shutdown_telemetry()
    logger.info("Disposing database connection pool...")
    await engine.dispose()
    logger.info("Application shutdown completed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise-grade production-ready User & Authentication microservice for E-Commerce.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------
# Middlewares
# ---------------------------------------------------------
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
    """
    Attaches a unique Request-ID, captures OpenTelemetry trace correlation headers,
    and measures request latency for performance monitoring.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = (time.perf_counter() - start_time) * 1000  # ms
    trace_id, span_id = get_current_trace_ids()

    response.headers["X-Request-ID"] = request_id
    if trace_id:
        response.headers["X-Trace-ID"] = trace_id
    if span_id:
        response.headers["X-Span-ID"] = span_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# ---------------------------------------------------------
# Centralized Global Exception Handlers
# ---------------------------------------------------------
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
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(
            {
                "field": field,
                "message": err.get("msg"),
                "type": err.get("type"),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "status_code": 422,
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed. Please check field requirements.",
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
            "message": "A database constraint violation occurred (e.g. duplicate key).",
            "details": None,
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
    logger.exception("Unhandled internal exception [request_id=%s, trace_id=%s]: %s", req_id, trace_id, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please contact system support.",
            "details": None,
            "meta": {
                "request_id": req_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "path": request.url.path,
            },
        },
    )


# ---------------------------------------------------------
# Health & Discovery Routes
# ---------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Health check verifying database liveness and service status."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
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


# Include V1 Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
