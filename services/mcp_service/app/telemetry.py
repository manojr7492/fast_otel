import logging
from typing import Optional
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, TraceIdRatioBased

from app.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)
_tracer_provider: Optional[TracerProvider] = None


def get_tracer(name: Optional[str] = None) -> trace.Tracer:
    tracer_name = name or settings.OTEL_SERVICE_NAME
    return trace.get_tracer(tracer_name, "1.0.0")


def setup_telemetry(app: Optional[FastAPI] = None) -> Optional[TracerProvider]:
    global _tracer_provider

    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry tracing is disabled.")
        return None

    try:
        resource = Resource.create({
            SERVICE_NAME: settings.OTEL_SERVICE_NAME,
            SERVICE_VERSION: "1.0.0",
            DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
            "service.framework": "fastapi",
            "service.ai_framework": "langchain",
            "mcp.transport": "stdio",
        })

        ratio = float(settings.OTEL_SAMPLING_RATIO)
        sampler = ALWAYS_ON if ratio >= 1.0 else (ALWAYS_OFF if ratio <= 0.0 else TraceIdRatioBased(ratio))
        tracer_provider = TracerProvider(resource=resource, sampler=sampler)

        endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
        if not endpoint.endswith("/v1/traces") and ":4318" in endpoint:
            endpoint = f"{endpoint.rstrip('/')}/v1/traces"

        exporter = HTTPSpanExporter(endpoint=endpoint)
        span_processor = BatchSpanProcessor(
            exporter,
            max_queue_size=2048,
            schedule_delay_millis=500,
            max_export_batch_size=512,
            export_timeout_millis=30000,
        )
        tracer_provider.add_span_processor(span_processor)

        trace.set_tracer_provider(tracer_provider)
        _tracer_provider = tracer_provider

        if app:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=tracer_provider,
                excluded_urls="health,docs,openapi.json,redoc",
            )
        HTTPXClientInstrumentor().instrument()

        logger.info("OpenTelemetry distributed tracing initialized for %s", settings.OTEL_SERVICE_NAME)
        return tracer_provider
    except Exception as exc:
        logger.warning("Failed to initialize OpenTelemetry tracing: %s", str(exc))
        return None


def shutdown_telemetry():
    global _tracer_provider
    if _tracer_provider:
        try:
            _tracer_provider.shutdown()
        except Exception:
            pass

