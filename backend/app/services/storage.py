"""Select local filesystem or private S3 storage per application setting."""
from app.core.config import settings
from app.services import local_storage as local
from app.services import aws_s3_storage as s3

InvalidUpload = local.InvalidUpload
UploadTooLarge = local.UploadTooLarge
MAX_FILE_SIZE = local.MAX_FILE_SIZE


def backend():
    return s3 if settings.storage_backend == "s3" else local


def save_file(stream, original_filename):
    return backend().save_file(stream, original_filename)


def file_exists(key):
    return backend().file_exists(key)


def delete_file(key):
    return backend().delete_file(key)


def pending_delete(key):
    return backend().pending_delete(key)


def open_file(key):
    if settings.storage_backend == "s3":
        return s3.open_file(key)
    return local.get_file_path(key).open("rb")


def available():
    if settings.storage_backend == "s3":
        return s3.available()
    local.STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    if not local.STORAGE_ROOT.is_dir():
        raise OSError("Storage directory unavailable")
