"""Local filesystem storage for development and tests."""
import re
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.core.config import PROJECT_ROOT

STORAGE_ROOT = PROJECT_ROOT / "backend" / "storage"
MAX_FILE_SIZE = 10 * 1024 * 1024


class InvalidUpload(ValueError):
    pass


class UploadTooLarge(InvalidUpload):
    pass


def get_file_path(storage_key: str) -> Path:
    # Accept only keys generated here, never arbitrary relative/absolute paths.
    if not re.fullmatch(r"documents/[0-9a-f-]{36}(?:\.[a-zA-Z0-9]{1,10})?", storage_key):
        raise ValueError("Invalid storage key")
    root = STORAGE_ROOT.resolve()
    path = (root / storage_key).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Invalid storage key")
    return path


def save_file(stream: BinaryIO, original_filename: str) -> tuple[str, int]:
    extension = Path(original_filename).suffix
    if not re.fullmatch(r"\.[a-zA-Z0-9]{1,10}", extension):
        extension = ""
    key = f"documents/{uuid4()}{extension}"
    path = get_file_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with path.open("xb") as target:
            while chunk := stream.read(64 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise UploadTooLarge("Maximum file size is 10 MiB")
                target.write(chunk)
        if size == 0:
            raise InvalidUpload("Empty files are not allowed")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return key, size


def file_exists(storage_key: str) -> bool:
    return get_file_path(storage_key).is_file()


def delete_file(storage_key: str) -> None:
    get_file_path(storage_key).unlink(missing_ok=True)


@contextmanager
def pending_delete(storage_key: str):
    """Keep file bytes recoverable until the metadata transaction commits."""
    path = get_file_path(storage_key)
    backup = path.with_name(f"{path.name}.{uuid4()}.pending")
    moved = False
    try:
        path.rename(backup)
        moved = True
    except FileNotFoundError:
        pass
    try:
        yield
    except Exception:
        if moved:
            backup.replace(path)
        raise
    else:
        if moved:
            backup.unlink()
