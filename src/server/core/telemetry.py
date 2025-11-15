"""OpenTelemetry configuration for distributed tracing."""

import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from ..config.settings import settings

logger = logging.getLogger(__name__)


def init_telemetry() -> None:
    """Initialize OpenTelemetry tracing and metrics."""

    if not settings.ENVIRONMENT == "production":
        logger.info("Telemetry disabled in non-production environment")
        return

    try:
        jaeger_exporter = JaegerExporter(
            agent_host_name=settings.JAEGER_HOST,
            agent_port=settings.JAEGER_PORT,
        )

        trace_provider = TracerProvider()
        trace_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        trace.set_tracer_provider(trace_provider)

        prometheus_reader = PrometheusMetricReader()
        meter_provider = MeterProvider(metric_readers=[prometheus_reader])
        metrics.set_meter_provider(meter_provider)

        FastAPIInstrumentor.instrument_app(
            app=None,
            excluded_urls=".*health.*",
        )
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        LoggingInstrumentor().instrument()

        logger.info("OpenTelemetry initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {str(e)}")


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance."""
    return metrics.get_meter(name)
