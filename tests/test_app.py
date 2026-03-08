import sys
from pathlib import Path

from prometheus_client import generate_latest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


def test_root_returns_hello_world():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.data == b"Hello, World!"


def test_request_duration_metric_is_registered():
    # Hitting the route once ensures the Summary metric is populated.
    app.test_client().get("/")

    metrics_output = generate_latest().decode("utf-8")
    assert "request_duration_seconds" in metrics_output
