import importlib
import logging

logger = logging.getLogger(__name__)


def _load_opentelemetry():
    try:
        trace_module = importlib.import_module("opentelemetry")
        trace = trace_module.trace

        sdk_trace_module = importlib.import_module("opentelemetry.sdk.trace")
        TracerProvider = sdk_trace_module.TracerProvider

        export_module = importlib.import_module("opentelemetry.sdk.trace.export")
        BatchSpanProcessor = export_module.BatchSpanProcessor
        ConsoleSpanExporter = export_module.ConsoleSpanExporter

        return trace, TracerProvider, BatchSpanProcessor, ConsoleSpanExporter
    except ModuleNotFoundError:
        return None, None, None, None


def setup_telemetry(service_name: str = "RGD-Alpha-Enterprise"):
    trace, TracerProvider, BatchSpanProcessor, ConsoleSpanExporter = (
        _load_opentelemetry()
    )

    if trace is None or TracerProvider is None:
        logger.warning("OpenTelemetry is not installed; tracing is disabled.")
        return logging.getLogger(service_name)

    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)
