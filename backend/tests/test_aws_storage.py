"""S3 behavior without AWS calls."""
from io import BytesIO

import pytest
from botocore.exceptions import ClientError

from app.core.config import Settings, settings
from app.services import aws_s3_storage as s3
from app.services import storage


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.fail_delete = False

    def put_object(self, Bucket, Key, Body):
        self.objects[Key] = bytes(Body)

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404", "Message": "missing"}}, "HeadObject")

    def get_object(self, Bucket, Key):
        self.head_object(Bucket, Key)
        return {"Body": BytesIO(self.objects[Key])}

    def delete_object(self, Bucket, Key):
        if self.fail_delete:
            raise ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}}, "DeleteObject")
        self.objects.pop(Key, None)

    def head_bucket(self, Bucket):
        return {}


@pytest.fixture
def fake_s3(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "aws_region", "ap-south-2")
    monkeypatch.setattr(settings, "s3_bucket_name", "test-documents")
    monkeypatch.setattr(s3, "client", lambda: fake)
    return fake


def test_backend_selection_and_default(monkeypatch):
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    assert Settings(_env_file=None).storage_backend == "local"
    monkeypatch.setattr(settings, "storage_backend", "local")
    assert storage.backend() is storage.local
    monkeypatch.setattr(settings, "storage_backend", "s3")
    assert storage.backend() is s3


def test_s3_upload_download_and_delete(fake_s3):
    key, size = storage.save_file(BytesIO(b"hello"), "report.txt")
    assert key.startswith("documents/") and key.endswith(".txt")
    assert size == 5
    assert storage.file_exists(key)
    assert storage.open_file(key).read() == b"hello"
    with storage.pending_delete(key):
        assert not storage.file_exists(key)
    assert not storage.file_exists(key)


def test_s3_rejects_invalid_upload(fake_s3):
    with pytest.raises(storage.InvalidUpload):
        storage.save_file(BytesIO(b""), "empty.txt")
    with pytest.raises(storage.UploadTooLarge):
        storage.save_file(BytesIO(b"x" * (storage.MAX_FILE_SIZE + 1)), "large.txt")
    assert fake_s3.objects == {}


def test_s3_delete_failure_preserves_object(fake_s3):
    key, _ = storage.save_file(BytesIO(b"hello"), "report.txt")
    fake_s3.fail_delete = True
    with pytest.raises(ClientError):
        with storage.pending_delete(key):
            pass
    assert storage.file_exists(key)


def test_s3_commit_failure_restores_object(fake_s3):
    key, _ = storage.save_file(BytesIO(b"hello"), "report.txt")
    with pytest.raises(RuntimeError):
        with storage.pending_delete(key):
            raise RuntimeError("commit failed")
    assert storage.open_file(key).read() == b"hello"


def test_s3_missing_and_access_error(fake_s3):
    assert not storage.file_exists("documents/missing")
    with pytest.raises(FileNotFoundError):
        storage.open_file("documents/missing")
    fake_s3.fail_delete = True
    with pytest.raises(ClientError):
        storage.delete_file("documents/missing")
