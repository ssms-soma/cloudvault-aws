# CloudVault backend

Minimal FastAPI application with a health endpoint and a document router reserved for the next AWS phase.

From `cloudvault-aws/`, create the local environment:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On macOS/Linux use `python3` to create the environment and `.venv/bin/python` to run it.

- Health: http://localhost:8000/health
- Interactive API docs: http://localhost:8000/docs
- Expected health response: `{"status":"ok","service":"cloudvault-api"}`

Optionally copy the project-root `.env.example` to `.env`. Settings load that file and environment variables; environment variables take precedence. Blank settings are valid for this phase.

The document router has no endpoints yet. Model, schema, database, and service modules are placeholders only. SQLAlchemy, psycopg, boto3, and python-multipart are included for the planned document integration; the application does not use them yet or contact AWS/PostgreSQL.

See [the project README](../README.md) for architecture, frontend setup, and security guidance. The `tests/` package is reserved for future tests.
