# CloudVault

Secure Cloud Document Management.

CloudVault has a working document API using FastAPI, SQLAlchemy 2.x,
PostgreSQL, and selectable local filesystem or private S3 storage. The React + Vite dashboard supports
document upload, listing, download, and deletion through the API.

**CloudVault is deployed and its health, upload, list, download, and delete flows have been verified on AWS.**

## Current features

- Upload files up to 10 MiB; validate filenames and reject empty uploads.
- List documents newest first, retrieve metadata, download, and delete.
- UUID-based disk filenames and relative storage keys in API responses.
- Cleanup of saved files when metadata insertion fails.
- Local CORS restricted to http://localhost:5173. Production can use a same-origin Nginx proxy.
- Health endpoint, interactive API docs, and focused backend tests.

## Architecture

| Component | Local development | AWS deployment |
| --- | --- | --- |
| Backend | Python 3.12+, FastAPI, Uvicorn | FastAPI under systemd on EC2 |
| Database | Local PostgreSQL, SQLAlchemy, psycopg | Amazon RDS PostgreSQL |
| Storage | Local filesystem by default; S3 selectable | Private Amazon S3 bucket |
| Frontend | React + Vite, Node.js 22.12+ | Static build served by Nginx on EC2 |
| Configuration | pydantic-settings, python-dotenv | EC2 environment file and IAM instance profile |

```text
Browser → EC2/Nginx → React static frontend
                    → /api and /health → FastAPI on 127.0.0.1:8000
                                         ├→ private RDS PostgreSQL
                                         └→ private S3 through EC2 IAM role
```

Terraform provisions a custom VPC, an Internet Gateway and route tables, one
public subnet for EC2, and two private subnets for the RDS DB subnet group.
Security Groups allow PostgreSQL port 5432 only from the EC2 group; RDS is not
publicly accessible. S3 Block Public Access is enabled. The EC2 IAM instance
profile grants bucket-scoped S3 access without static AWS keys. AWS CLI and
Systems Manager (SSM) were used for deployment and verification.

Local file storage is backend/storage/documents/. Set STORAGE_BACKEND=s3 with
AWS_REGION and S3_BUCKET_NAME to use private S3 through boto3's credential chain.
On EC2, the instance profile supplies credentials; do not put AWS access keys in .env.

## Local Backend Setup

### 1. Start PostgreSQL and create a database

PostgreSQL must be running locally. In PowerShell, connect using your existing
administrator password (adjust the installation path/version if needed):

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -U postgres -d postgres
```

For a new role/database, run in psql:

```sql
CREATE ROLE cloudvault_user LOGIN;
\password cloudvault_user
CREATE DATABASE cloudvault OWNER cloudvault_user;
\q
```

The \password command prompts for your chosen password without embedding it in
SQL. If the role or database exists, reuse it instead of running CREATE again.
On macOS/Linux use psql -h localhost -U postgres -d postgres.

### 2. Create the environment file

From the project root:

```powershell
Copy-Item .env.example .env
```

Edit the project-root .env to contain:

```dotenv
DATABASE_URL=postgresql+psycopg://cloudvault_user:YOUR_LOCAL_PASSWORD@localhost:5432/cloudvault
AWS_REGION=
S3_BUCKET_NAME=
STORAGE_BACKEND=local
```

Replace YOUR_LOCAL_PASSWORD with the password you set. URL-encode special
characters in the password (for example @ becomes %40). This is a placeholder,
not a working credential. Leave AWS settings blank. Environment variables
override the project-root .env file.

### 3. Install dependencies and start FastAPI

From the project root in PowerShell:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On macOS/Linux use python3 to create the venv, backend/.venv/bin/python for
installation, and .venv/bin/python when inside backend/.

Startup requires a valid PostgreSQL connection and creates missing tables with
Base.metadata.create_all(). It does not migrate existing tables; Alembic can be
introduced when migrations are needed. Storage folders are created on first upload.

### 4. Try the API

Open http://localhost:8000/docs to try uploads and document operations.

| Method | Path | Success |
| --- | --- | --- |
| GET | /health | 200 when database and selected storage are available; otherwise 503 |
| POST | /api/documents | 201, multipart field named file |
| GET | /api/documents | 200, newest first |
| GET | /api/documents/{id} | 200, metadata |
| GET | /api/documents/{id}/download | 200, attachment |
| DELETE | /api/documents/{id} | 200, deletion confirmation |

```powershell
curl.exe http://localhost:8000/health
curl.exe -F "file=@C:/path/to/report.pdf" http://localhost:8000/api/documents
curl.exe http://localhost:8000/api/documents
curl.exe http://localhost:8000/api/documents/1
curl.exe http://localhost:8000/api/documents/1/download -o downloaded-report.pdf
curl.exe -X DELETE http://localhost:8000/api/documents/1
```

Missing documents/files return 404; invalid/empty files return 400; missing
multipart fields return 422; oversized files return 413. Database errors return
503 and filesystem errors return 500, with generic messages. Health checks
database connectivity and selected storage availability on each request.

## Tests

From backend/:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q
```

Tests use an in-memory SQLite database and temporary storage, overriding the
session dependency and bypassing PostgreSQL startup. They verify health,
validation, file round trips, ordering, missing metadata/files, failure cleanup,
path rejection, local CORS, and mocked S3 operations. They do not validate PostgreSQL connectivity,
timezone behavior, or PostgreSQL startup table creation. Verify those through
the running API after configuring your local database.

## Frontend

From frontend/:

```powershell
npm.cmd ci
npm.cmd run dev -- --port 5173 --strictPort
npm.cmd run build
```

Use npm on macOS/Linux. Open the URL printed by Vite, usually
http://localhost:5173. Start the backend in a separate terminal first.
The Vite dev server proxies /api to http://127.0.0.1:8000. Keep the frontend on
port 5173 to match the backend's local CORS origin. `VITE_API_BASE_URL` can
override the API origin; leave it unset for local proxying and same-origin EC2.

Choose or drop one file, then click Upload document. The dashboard validates
empty files and the 10 MiB limit, shows loading/success/error feedback, and
refreshes the document list after uploads and deletions. Documents show their
original filename, type, readable size, and local upload date/time. Downloads
preserve the original filename; deletion asks for confirmation. Use Refresh
to retry if the API is temporarily unavailable.

## Infrastructure as Code

[Terraform](infrastructure/terraform/README.md) provisions the VPC, networking,
EC2, private RDS PostgreSQL, private S3, IAM, and Security Groups. RDS remains
single-AZ and no NAT Gateway or load balancer is used. Nginx serves React and
proxies the API to a loopback Uvicorn process managed by systemd. The
[deployment files](deployment/README.md) document the EC2 service configuration.

## Project directories

- backend/app/api/routes/: document endpoints.
- backend/app/models/ and schemas/: ORM and public response definitions.
- backend/app/db/: declarative base and synchronous sessions.
- backend/app/services/: metadata operations, local file storage, and private S3 storage.
- backend/tests/: focused API tests.
- frontend/: React document dashboard and centralized API client.
- architecture/, screenshots/, docs/: tracked documentation folders.

## Security and limitations

Never commit credentials. .env and backend/storage/ are ignored by Git. The
.env.example contains a placeholder URL only. Local mode needs no AWS credentials;
S3 mode uses the standard boto3 credential chain and the EC2 instance profile.
API responses contain relative keys, never absolute filesystem paths. Original
filenames are never used as disk filenames. Downloads are binary attachments;
client-provided MIME metadata is not trusted for rendering.

There is no authentication. Keep local Uvicorn bound to loopback and restrict
public demo access. The 10 MiB limit
applies while copying parsed uploads to storage, not to network request bodies.
Filesystem and database operations are not one atomic transaction. A process
crash or failed cleanup can leave them inconsistent. Deletion temporarily renames
the file and restores it if the metadata commit fails. A crash during that window
or failed final removal can leave a .pending file requiring manual reconciliation.
Reconciliation, network request limits, and production access controls are later work.
