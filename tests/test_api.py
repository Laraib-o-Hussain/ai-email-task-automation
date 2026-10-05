import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(settings, "ai_mode", "mock")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def _override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["ai_mode"] == "mock"


def test_extract_task_mock(client):
    r = client.post(
        "/extract-task",
        json={
            "message": "Please remind Sarah to prepare the monthly sales report by Friday at 3 PM."
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "sales report" in body["task"].lower()
    assert body["assignee"] == "Sarah"
    assert body["due_date"] is not None
    assert body["due_time"] == "15:00"


def test_create_task(client):
    r = client.post(
        "/tasks",
        json={
            "title": "Prepare the monthly sales report",
            "assignee": "Sarah",
            "due_date": "2026-10-10",
            "due_time": "15:00",
            "priority": "high",
        },
    )
    assert r.status_code == 201
    assert r.json()["assignee"] == "Sarah"


def test_list_and_get_task(client):
    created = client.post(
        "/tasks",
        json={"title": "Call vendor", "assignee": "Alex", "priority": "low"},
    ).json()

    listed = client.get("/tasks")
    assert listed.status_code == 200
    assert any(t["id"] == created["id"] for t in listed.json())

    one = client.get(f"/tasks/{created['id']}")
    assert one.status_code == 200
    assert one.json()["title"] == "Call vendor"


def test_update_task(client):
    created = client.post(
        "/tasks",
        json={"title": "Draft outline", "assignee": "Nora", "priority": "medium"},
    ).json()
    r = client.put(f"/tasks/{created['id']}", json={"priority": "high", "assignee": "Sam"})
    assert r.status_code == 200
    assert r.json()["priority"] == "high"
    assert r.json()["assignee"] == "Sam"


def test_delete_task(client):
    created = client.post(
        "/tasks",
        json={"title": "Temp task", "assignee": "Lee", "priority": "low"},
    ).json()
    r = client.delete(f"/tasks/{created['id']}")
    assert r.status_code == 200
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_invalid_extract_input(client):
    r = client.post("/extract-task", json={"message": "hi"})
    assert r.status_code == 422


def test_invalid_task_date(client):
    r = client.post(
        "/tasks",
        json={
            "title": "Broken date",
            "assignee": "Sam",
            "due_date": "10/10/2026",
            "priority": "medium",
        },
    )
    assert r.status_code == 422


def test_mock_ai_mode_via_health(client):
    assert client.get("/health").json()["ai_mode"] == "mock"
