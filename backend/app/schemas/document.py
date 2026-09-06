"""Public document metadata without filesystem paths."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str | None
    file_size: int
    storage_key: str
    uploaded_at: datetime
