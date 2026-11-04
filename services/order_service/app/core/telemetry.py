import logging
from typing import Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    TraceIdRatioBased,
)
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)
_tracer_provider: Optional[TracerProvider] = None


def get_tracer(name: Optional[str] = None) -> trace.Tracer:
    tracer_name = name or settings.OTEL_SERVICE_NAME
    return trace.get_tracer(tracer_name, "1.0.0")


def setup_telemetry(
    app: Optional[FastAPI] = None,
    engine: Optional[AsyncEngine] = None,
) -> Optional[TracerProvider]:
    global _tracer_provider

    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry tracing is disabled via configuration.")
        return None

    try:
        resource = Resource.create(
            {
                SERVICE_NAME: settings.OTEL_SERVICE_NAME,
                SERVICE_VERSION: "1.0.0",
                DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
                "service.framework": "fastapi",
                "telemetry.sdk.language": "python",
            }
        )

        ratio = float(settings.OTEL_SAMPLING_RATIO)
        sampler = ALWAYS_ON if ratio >= 1.0 else (ALWAYS_OFF if ratio <= 0.0 else TraceIdRatioBased(ratio))

        tracer_provider = TracerProvider(resource=resource, sampler=sampler)

        protocol = settings.OTEL_EXPORTER_OTLP_PROTOCOL.lower()
        endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT

        if protocol == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter as GRPCSpanExporter,
            )
            grpc_endpoint = endpoint.replace("http://", "").replace("https://", "")
            if ":4318" in grpc_endpoint:
                grpc_endpoint = grpc_endpoint.replace(":4318", ":4317")
            grpc_endpoint = grpc_endpoint.split("/")[0]
            exporter = GRPCSpanExporter(endpoint=grpc_endpoint, insecure=True)
            logger.info("Configured OTLP gRPC Span Exporter to endpoint: %s", grpc_endpoint)
        else:
            if not endpoint.endswith("/v1/traces") and ":4318" in endpoint:
                endpoint = f"{endpoint.rstrip('/')}/v1/traces"
            exporter = HTTPSpanExporter(endpoint=endpoint)
            logger.info("Configured OTLP HTTP Span Exporter to endpoint: %s", endpoint)

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

        set_global_textmap(
            CompositePropagator(
                [
                    TraceContextTextMapPropagator(),
                    W3CBaggagePropagator(),
                ]
            )
        )

        if app is not None:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=tracer_provider,
                excluded_urls="health,healthz,metrics,docs,redoc,openapi.json",
            )
            logger.info("FastAPI application instrumented with OpenTelemetry.")

        HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)

        if engine is not None and hasattr(engine, "sync_engine"):
            try:
                SQLAlchemyInstrumentor().instrument(
                    engine=engine.sync_engine,
                    tracer_provider=tracer_provider,
                )
                logger.info("SQLAlchemy engine instrumented with OpenTelemetry.")
            except Exception as sql_err:
                logger.warning("Could not instrument SQLAlchemy engine: %s", sql_err)

        LoggingInstrumentor().instrument(set_logging_format=False)

        logger.info(
            "OpenTelemetry distributed tracing successfully initialized for %s.",
            settings.OTEL_SERVICE_NAME,
        )
        return tracer_provider

    except Exception as exc:
        logger.error(
            "Failed to initialize OpenTelemetry tracing: %s. Service will continue without tracing.",
            exc,
            exc_info=True,
        )
        return None


def shutdown_telemetry() -> None:
    global _tracer_provider
    if _tracer_provider is not None:
        try:
            logger.info("Flushing and shutting down OpenTelemetry TracerProvider...")
            _tracer_provider.shutdown()
            logger.info("OpenTelemetry TracerProvider shutdown complete.")
        except Exception as exc:
            logger.warning("Error during OpenTelemetry TracerProvider shutdown: %s", exc)
        finally:
            _tracer_provider = None

