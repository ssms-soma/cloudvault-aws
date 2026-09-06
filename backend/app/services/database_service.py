"""Small metadata operations. Routes own transaction commits."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def create_document(db: Session, **metadata) -> Document:
    document = Document(**metadata)
    db.add(document)
    db.flush()
    db.refresh(document)
    return document


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(
        Document.uploaded_at.desc(), Document.id.desc()
    )))


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)


def delete_document(db: Session, document: Document) -> None:
    db.delete(document)
    db.flush()
