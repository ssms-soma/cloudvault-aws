"""API behavior with SQLite and temporary files; not PostgreSQL integration tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services import database_service as database
from app.services import s3_service as storage


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)

    def override_db():
        with Session(engine, expire_on_commit=False) as db:
            try:
                yield db
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = override_db
    # Deliberately bypass PostgreSQL startup; this suite only tests API behavior.
    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()
        engine.dispose()


def upload(client, content=b"hello", filename="report.txt"):
    return client.post("/api/documents", files={"file": (filename, content, "text/plain")})


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cloudvault-api"}


@pytest.mark.parametrize("method,path", [
    ("get", "/api/documents/999"),
    ("get", "/api/documents/999/download"),
    ("delete", "/api/documents/999"),
])
def test_missing_document(client, method, path):
    assert getattr(client, method)(path).status_code == 404


def test_empty_upload(client, tmp_path):
    assert upload(client, b"").status_code == 400
    assert not list(tmp_path.rglob("*.*"))
    assert client.get("/api/documents").json() == []


def test_filename_required(client):
    assert upload(client, filename=" ").status_code == 400
    assert client.post("/api/documents").status_code == 422


def test_oversized_upload(client, tmp_path):
    response = upload(client, b"x" * (storage.MAX_FILE_SIZE + 1))
    assert response.status_code == 413
    assert not list(tmp_path.rglob("*.*"))


def test_document_lifecycle(client, tmp_path):
    response = upload(client, filename="../../report.txt")
    assert response.status_code == 201
    document = response.json()
    assert document["original_filename"] == "report.txt"
    assert document["file_size"] == 5
    assert document["storage_key"].startswith("documents/")
    assert document["storage_key"] != "documents/report.txt"
    assert str(tmp_path) not in response.text
    assert "stored_filename" not in document
    second = upload(client).json()
    assert second["storage_key"] != document["storage_key"]
    assert [d["id"] for d in client.get("/api/documents").json()] == [second["id"], document["id"]]
    url = f'/api/documents/{document["id"]}'
    assert client.get(url).json() == document
    download = client.get(url + "/download")
    assert download.status_code == 200
    assert download.content == b"hello"
    assert 'filename="report.txt"' in download.headers["content-disposition"]
    assert client.delete(url).status_code == 200
    assert client.get(url).status_code == 404
    assert not storage.file_exists(document["storage_key"])


def test_missing_file(client):
    document = upload(client).json()
    storage.delete_file(document["storage_key"])
    assert client.get(f'/api/documents/{document["id"]}/download').status_code == 404
    assert client.delete(f'/api/documents/{document["id"]}').status_code == 200


@pytest.mark.parametrize("stage", ["insert", "commit"])
def test_database_failure_removes_upload(client, tmp_path, monkeypatch, stage):
    def fail(*args, **kwargs):
        raise SQLAlchemyError("sensitive connection information")

    if stage == "insert":
        monkeypatch.setattr(database, "create_document", fail)
    else:
        monkeypatch.setattr(Session, "commit", fail)
    response = upload(client)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database operation failed"}
    assert not list(tmp_path.rglob("*.*"))
    assert client.get("/api/documents").json() == []


def test_storage_failure(client, monkeypatch):
    def fail(*args):
        raise OSError("sensitive local path")

    monkeypatch.setattr(storage, "save_file", fail)
    response = upload(client)
    assert response.status_code == 500
    assert response.json() == {"detail": "File storage operation failed"}


def test_delete_commit_failure_preserves_file(client, monkeypatch):
    document = upload(client).json()

    def fail(*args):
        raise SQLAlchemyError("sensitive connection information")

    monkeypatch.setattr(Session, "commit", fail)
    url = f'/api/documents/{document["id"]}'
    assert client.delete(url).status_code == 503
    assert client.get(url).status_code == 200
    assert client.get(url + "/download").content == b"hello"


def test_delete_storage_failure_preserves_metadata(client, monkeypatch):
    document = upload(client).json()

    def fail(*args):
        raise OSError("sensitive local path")

    monkeypatch.setattr(storage, "pending_delete", fail)
    url = f'/api/documents/{document["id"]}'
    assert client.delete(url).status_code == 500
    assert client.get(url).status_code == 200
    assert client.get(url + "/download").content == b"hello"


@pytest.mark.parametrize("key", ["../secret", "documents/../../secret", "C:/secret", "/etc/passwd"])
def test_storage_rejects_paths(key):
    with pytest.raises(ValueError):
        storage.get_file_path(key)


def test_local_cors(client):
    response = client.options("/api/documents", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.options("/api/documents", headers={
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
    })
    assert "access-control-allow-origin" not in response.headers
