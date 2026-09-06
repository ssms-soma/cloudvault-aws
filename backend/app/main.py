"""CloudVault API entry point."""

from fastapi import FastAPI

from app.api.routes.document_routes import router as document_router
from app.core.config import settings

app = FastAPI(title="CloudVault API", version="0.1.0")
app.state.settings = settings
app.include_router(document_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Report API availability without contacting external services."""
    return {"status": "ok", "service": "cloudvault-api"}
