"""Document upload, metadata, download, and deletion."""
from pathlib import PurePosixPath
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentResponse
from app.services import database_service as database
from app.services import storage

router = APIRouter(prefix="/api/documents", tags=["documents"])
Database = Annotated[Session, Depends(get_db)]


def require_document(db: Session, document_id: int):
    document = database.get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("", response_model=DocumentResponse, status_code=201)
def upload_document(db: Database, file: Annotated[UploadFile, File()]):
    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not filename or filename in {".", ".."} or len(filename) > 255:
        raise HTTPException(status_code=400, detail="A filename of 1–255 characters is required")
    if any(ord(char) < 32 or ord(char) == 127 for char in filename):
        raise HTTPException(status_code=400, detail="Filename contains invalid characters")
    if file.content_type and len(file.content_type) > 255:
        raise HTTPException(status_code=400, detail="Content type is too long")
    try:
        key, size = storage.save_file(file.file, filename)
    except storage.UploadTooLarge:
        raise HTTPException(status_code=413, detail="Maximum file size is 10 MiB") from None
    except storage.InvalidUpload:
        raise HTTPException(status_code=400, detail="Empty files are not allowed") from None
    try:
        document = database.create_document(
            db, original_filename=filename,
            stored_filename=PurePosixPath(key).name,
            content_type=file.content_type, file_size=size, storage_key=key,
        )
        response = DocumentResponse.model_validate(document)
        db.commit()
    except Exception:
        try:
            db.rollback()
        finally:
            storage.delete_file(key)
        raise
    return response


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Database):
    return database.list_documents(db)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Database):
    return require_document(db, document_id)


@router.get("/{document_id}/download")
def download_document(document_id: int, db: Database):
    document = require_document(db, document_id)
    try:
        body = storage.open_file(document.storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document file not found")

    def chunks():
        try:
            while chunk := body.read(64 * 1024):
                yield chunk
        finally:
            body.close()

    name = document.original_filename
    fallback = name.encode("ascii", "ignore").decode().replace('"', "") or "download"
    disposition = f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{quote(name)}'
    return StreamingResponse(
        chunks(), media_type="application/octet-stream",
        headers={"Content-Disposition": disposition},
    )


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Database):
    document = require_document(db, document_id)
    database.delete_document(db, document)
    with storage.pending_delete(document.storage_key):
        db.commit()
    return {"status": "deleted", "id": document_id}
