import os

from flask import Flask
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Summary, start_http_server

app = Flask(__name__)
metrics = Summary('request_duration_seconds', 'Duration of requests in seconds')
tracer = trace.get_tracer(__name__)


def setup_tracing() -> None:
    resource = Resource.create({SERVICE_NAME: "flask-app"})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"),
        insecure=True,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

@app.route('/')
@metrics.time()
def hello():
    with tracer.start_as_current_span("GET /"):
        return 'Hello, World! RAKESH WORLD!'

if __name__ == '__main__':
    setup_tracing()
    start_http_server(8000)
    app.run(host='0.0.0.0')
