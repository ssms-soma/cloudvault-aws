"""Router reserved for document endpoints in the next AWS phase."""

from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])
