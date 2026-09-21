# CloudVault backend

FastAPI document API using PostgreSQL metadata and selectable filesystem or
private S3 storage. Local filesystem storage is the default. Follow
[Local Backend Setup](../README.md#local-backend-setup)
to create the PostgreSQL role/database and project-root .env first.

From this directory in PowerShell:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://localhost:8000/docs. Health: http://localhost:8000/health.
Document upload, list, metadata, download, and delete are under /api/documents.
Startup creates missing tables but does not migrate existing tables.
Local files are stored in backend/storage/documents/ and ignored by Git.
For AWS mode, set STORAGE_BACKEND=s3, AWS_REGION, S3_BUCKET_NAME, and an RDS
DATABASE_URL. EC2 should obtain AWS credentials from its instance profile.

Run focused tests:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q
```

Tests use isolated SQLite and temporary files and do not verify PostgreSQL.
See the root README for setup, endpoints, limitations, and planned architecture.
