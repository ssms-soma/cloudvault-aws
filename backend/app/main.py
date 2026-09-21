"""CloudVault API entry point."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.orm import Session
from botocore.exceptions import BotoCoreError, ClientError

from app.api.routes.document_routes import router as document_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_engine, get_db
from app.services import storage
from app.models.document import Document  # Register table metadata before create_all.


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError:
        engine.dispose()
        raise RuntimeError("Database startup failed. Check local PostgreSQL and DATABASE_URL.") from None
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="CloudVault API", version="0.2.0", lifespan=lifespan)
app.state.settings = settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(document_router)


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"detail": "Database operation failed"})


@app.exception_handler(OSError)
async def storage_error(request: Request, exc: OSError):
    return JSONResponse(status_code=500, content={"detail": "File storage operation failed"})


@app.exception_handler(BotoCoreError)
@app.exception_handler(ClientError)
async def s3_error(request: Request, exc: Exception):
    return JSONResponse(status_code=503, content={"detail": "File storage operation failed"})


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    """Check database and selected storage without returning connection details."""
    database_status = "connected"
    storage_status = "available"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"
    try:
        storage.available()
    except Exception:
        storage_status = "unavailable"
    result = {"status": "healthy" if database_status == "connected" and storage_status == "available" else "unhealthy",
              "database": database_status, "storage": storage_status}
    return result if result["status"] == "healthy" else JSONResponse(status_code=503, content=result)
