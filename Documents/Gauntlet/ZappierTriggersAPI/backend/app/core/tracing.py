"""
OpenTelemetry Tracing Configuration.

Provides distributed tracing with correlation across services.
Supports export to AWS X-Ray, Jaeger, or OTLP collectors.
"""

import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_tracing(app=None) -> None:
    """
    Configure OpenTelemetry tracing for the application.

    Args:
        app: FastAPI application instance (optional, for instrumentation)
    """
    if not settings.ENABLE_TRACING:
        logger.info("Tracing is disabled")
        return

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: settings.APP_NAME,
        SERVICE_VERSION: settings.APP_VERSION,
        "deployment.environment": settings.APP_ENV,
        "service.namespace": "zapier-triggers",
    })

    # Configure sampling (sample 100% in dev, configurable in prod)
    sampling_rate = 1.0 if settings.is_development else settings.TRACING_SAMPLE_RATE
    sampler = TraceIdRatioBased(sampling_rate)

    # Create tracer provider
    provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Configure exporter based on settings
    if settings.TRACING_EXPORTER == "otlp":
        # OTLP exporter (works with Jaeger, AWS X-Ray, etc.)
        exporter = OTLPSpanExporter(
            endpoint=settings.OTLP_ENDPOINT,
            insecure=not settings.is_production,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"OTLP trace exporter configured: {settings.OTLP_ENDPOINT}")

    elif settings.TRACING_EXPORTER == "xray":
        # AWS X-Ray propagation
        set_global_textmap(AwsXRayPropagator())
        # X-Ray exporter via OTLP
        exporter = OTLPSpanExporter(
            endpoint=settings.OTLP_ENDPOINT or "localhost:4317",
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("AWS X-Ray tracing configured")

    elif settings.TRACING_EXPORTER == "console":
        # Console exporter for development
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("Console trace exporter configured")

    else:
        # Default: W3C trace context propagation, no export
        set_global_textmap(TraceContextTextMapPropagator())
        logger.info("Tracing configured without exporter")

    # Set the global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument libraries
    _instrument_libraries(app)

    logger.info(
        f"Tracing initialized",
        extra={
            "exporter": settings.TRACING_EXPORTER,
            "sample_rate": sampling_rate,
        },
    )


def _instrument_libraries(app=None) -> None:
    """Instrument common libraries for automatic tracing."""
    # FastAPI instrumentation
    if app is not None:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,ready,live,metrics,docs,redoc,openapi",
        )
        logger.debug("FastAPI instrumented")

    # HTTPX (async HTTP client) instrumentation
    HTTPXClientInstrumentor().instrument()
    logger.debug("HTTPX instrumented")

    # Redis instrumentation
    RedisInstrumentor().instrument()
    logger.debug("Redis instrumented")


def instrument_sqlalchemy(engine) -> None:
    """
    Instrument SQLAlchemy engine for tracing.

    Call this after creating the database engine.
    """
    if not settings.ENABLE_TRACING:
        return

    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
        enable_commenter=True,
    )
    logger.debug("SQLAlchemy instrumented")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance for manual instrumentation.

    Args:
        name: Tracer name (usually __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def get_current_span() -> Span:
    """Get the currently active span."""
    return trace.get_current_span()


def get_trace_id() -> str | None:
    """
    Get the current trace ID as a string.

    Returns:
        Trace ID hex string or None if no active trace
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_span_id() -> str | None:
    """
    Get the current span ID as a string.

    Returns:
        Span ID hex string or None if no active span
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return None


def add_span_attributes(attributes: dict[str, Any]) -> None:
    """
    Add attributes to the current span.

    Args:
        attributes: Dictionary of attribute key-value pairs
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception, attributes: dict[str, Any] | None = None) -> None:
    """
    Record an exception in the current span.

    Args:
        exception: The exception to record
        attributes: Additional attributes to add
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception, attributes=attributes)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


def set_span_status(status: StatusCode, description: str = "") -> None:
    """
    Set the status of the current span.

    Args:
        status: Status code (OK, ERROR, UNSET)
        description: Optional status description
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_status(Status(status, description))


class SpanContext:
    """
    Context manager for creating spans with automatic error handling.

    Usage:
        with SpanContext("operation_name", attributes={"key": "value"}) as span:
            # Do work
            span.set_attribute("result", "success")
    """

    def __init__(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    ):
        self.name = name
        self.attributes = attributes or {}
        self.kind = kind
        self.span = None
        self.tracer = get_tracer()

    def __enter__(self) -> Span:
        self.span = self.tracer.start_span(
            name=self.name,
            kind=self.kind,
            attributes=self.attributes,
        )
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_val:
                self.span.record_exception(exc_val)
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            else:
                self.span.set_status(Status(StatusCode.OK))
            self.span.end()
        return False


# Decorator for tracing functions
def traced(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    Decorator to automatically trace a function.

    Args:
        name: Span name (defaults to function name)
        attributes: Static attributes to add to the span
        kind: Span kind

    Usage:
        @traced("my_operation", attributes={"component": "service"})
        async def my_function():
            pass
    """
    def decorator(func):
        import functools
        import asyncio

        span_name = name or func.__name__
        static_attributes = attributes or {}

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(
                span_name,
                kind=kind,
                attributes=static_attributes,
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(
                span_name,
                kind=kind,
                attributes=static_attributes,
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
