"""Private S3 document objects. Credentials come from boto3's normal provider chain."""
from contextlib import contextmanager
from pathlib import Path
import re
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.local_storage import InvalidUpload, UploadTooLarge, MAX_FILE_SIZE


def client():
    if not settings.s3_bucket_name or not settings.aws_region:
        raise RuntimeError("S3_BUCKET_NAME and AWS_REGION are required for S3 storage")
    return boto3.client("s3", region_name=settings.aws_region)


def save_file(stream, original_filename):
    extension = Path(original_filename).suffix
    if not re.fullmatch(r"\.[a-zA-Z0-9]{1,10}", extension):
        extension = ""
    key = f"documents/{uuid4()}{extension}"
    data = stream.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise UploadTooLarge("Maximum file size is 10 MiB")
    if not data:
        raise InvalidUpload("Empty files are not allowed")
    client().put_object(Bucket=settings.s3_bucket_name, Key=key, Body=data)
    return key, len(data)


def file_exists(key):
    try:
        client().head_object(Bucket=settings.s3_bucket_name, Key=key)
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def open_file(key):
    try:
        return client().get_object(Bucket=settings.s3_bucket_name, Key=key)["Body"]
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            raise FileNotFoundError(key) from None
        raise


def delete_file(key):
    client().delete_object(Bucket=settings.s3_bucket_name, Key=key)


@contextmanager
def pending_delete(key):
    # Keep a bounded copy so a failed DB commit can restore the object.
    try:
        body = open_file(key)
    except FileNotFoundError:
        body = None
    data = None
    if body is not None:
        try:
            data = body.read(MAX_FILE_SIZE + 1)
            if len(data) > MAX_FILE_SIZE:
                raise RuntimeError("Stored object exceeds recovery limit")
        finally:
            body.close()
        delete_file(key)
    try:
        yield
    except Exception:
        if data is not None:
            client().put_object(Bucket=settings.s3_bucket_name, Key=key, Body=data)
        raise


def available():
    client().head_bucket(Bucket=settings.s3_bucket_name)
