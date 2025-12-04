"""Unit tests for background tasks routes (/tasks)."""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.server.features.tasks.routes import router, TaskSubmitRequest
from src.server.tasks import analyze_demo_task, analyze_player_task, send_email_task
from src.server.celery_app import celery_app


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


class DummyResult:
    def __init__(self, status="PENDING", result=None, info=None, ready=False, successful=False):
        self.status = status
        self.result = result
        self.info = info
        self._ready = ready
        self._successful = successful

    def ready(self):  # pragma: no cover - trivial pass-through
        return self._ready

    def successful(self):  # pragma: no cover - trivial pass-through
        return self._successful


def test_submit_task_analyze_demo_success(client, monkeypatch):
    dummy_task = SimpleNamespace(id="task-1")
    monkeypatch.setattr(analyze_demo_task, "delay", lambda *_, **__: dummy_task)

    payload = {
        "task_type": "analyze_demo",
        "params": {"demo_path": "/tmp/demo.dem", "user_id": "123"},
    }

    response = client.post("/tasks/submit", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-1"
    assert body["task_type"] == "analyze_demo"
    assert body["status"] == "submitted"


def test_submit_task_analyze_player_success(client, monkeypatch):
    dummy_task = SimpleNamespace(id="task-2")
    monkeypatch.setattr(analyze_player_task, "delay", lambda *_, **__: dummy_task)

    payload = {
        "task_type": "analyze_player",
        "params": {"player_nickname": "test_player"},
    }

    response = client.post("/tasks/submit", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-2"
    assert body["task_type"] == "analyze_player"


def test_submit_task_send_email_success(client, monkeypatch):
    dummy_task = SimpleNamespace(id="task-3")
    monkeypatch.setattr(send_email_task, "delay", lambda *_, **__: dummy_task)

    payload = {
        "task_type": "send_email",
        "params": {"to_email": "user@example.com", "subject": "Hi", "body": "Test"},
    }

    response = client.post("/tasks/submit", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-3"
    assert body["task_type"] == "send_email"


def test_submit_task_unknown_type_returns_400(client):
    payload = {
        "task_type": "unknown_type",
        "params": {},
    }

    response = client.post("/tasks/submit", json=payload)

    assert response.status_code == 400
    assert "Unknown task type" in response.json()["detail"]


def test_submit_task_internal_error_returns_500(client, monkeypatch):
    def boom(*_, **__):  # noqa: ARG001, ARG002
        raise RuntimeError("boom")

    monkeypatch.setattr(analyze_demo_task, "delay", boom)

    payload = {
        "task_type": "analyze_demo",
        "params": {"demo_path": "/tmp/demo.dem", "user_id": "123"},
    }

    response = client.post("/tasks/submit", json=payload)

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to submit task"


def test_get_task_status_pending(client, monkeypatch):
    dummy_result = DummyResult(status="PENDING", ready=False)
    monkeypatch.setattr(celery_app, "AsyncResult", lambda task_id: dummy_result)

    response = client.get("/tasks/status/abc123")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "abc123"
    assert data["status"] == "PENDING"
    assert data["result"] is None
    assert data["error"] is None


def test_get_task_status_success_with_result(client, monkeypatch):
    dummy_result = DummyResult(
        status="SUCCESS",
        result={"status": "completed"},
        ready=True,
        successful=True,
    )
    monkeypatch.setattr(celery_app, "AsyncResult", lambda task_id: dummy_result)

    response = client.get("/tasks/status/task-ok")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["result"] == {"status": "completed"}
    assert data["error"] is None


def test_get_task_status_failure_with_error(client, monkeypatch):
    dummy_result = DummyResult(
        status="FAILURE",
        info="Boom",
        ready=True,
        successful=False,
    )
    monkeypatch.setattr(celery_app, "AsyncResult", lambda task_id: dummy_result)

    response = client.get("/tasks/status/task-fail")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILURE"
    assert data["result"] is None
    assert data["error"] == "Boom"


def test_get_task_status_internal_error_returns_500(client, monkeypatch):
    def boom(task_id):  # noqa: ARG001
        raise RuntimeError("boom")

    monkeypatch.setattr(celery_app, "AsyncResult", boom)

    response = client.get("/tasks/status/task-err")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get task status"
