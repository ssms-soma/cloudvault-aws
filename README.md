# CloudVault

Secure Cloud Document Management.

CloudVault is a document management application foundation built with FastAPI and React. The current phase provides a working local API and a static dashboard for review. Uploads, persistence, and cloud security controls are not implemented.

**AWS infrastructure will be added in the next phase. No AWS resources are provisioned by this project.**

## Planned AWS architecture

```text
Internet → EC2/FastAPI → private RDS PostgreSQL
           EC2/FastAPI → private S3 bucket
```

The planned VPC will contain public and private subnets. EC2 will host FastAPI in a public subnet, with RDS PostgreSQL in private subnets for document metadata. Document files will be stored in a private S3 bucket; S3 is an AWS service outside the VPC subnets. An IAM role will provide EC2 with scoped access to the bucket. Network access rules and deployment details will be designed in the next phase.

## Tech stack

- Backend: Python 3.12+, FastAPI, Uvicorn
- Frontend: React, Vite, JavaScript, CSS; Node.js 22.12+ (Node.js 24 supported)
- Configuration: pydantic-settings and python-dotenv
- Planned persistence: SQLAlchemy, psycopg, RDS PostgreSQL
- Planned storage: S3 through boto3; python-multipart for uploads
- Planned infrastructure: VPC, public/private subnets, EC2, RDS, S3, IAM

## Current features

- `GET /health` returns `{"status":"ok","service":"cloudvault-api"}`.
- FastAPI interactive API documentation at `/docs`.
- Registered document router reserved for future endpoints (currently has no routes).
- Environment-based configuration with no external connections at startup.
- CloudVault dashboard with a disabled upload placeholder and empty documents section.

## Planned features

- Document upload, listing, download, and deletion.
- Document metadata stored in PostgreSQL.
- Private file storage in S3 with scoped IAM access.
- AWS network and application deployment in the next phase.

## Project structure

- `backend/`: FastAPI application and clearly marked future integration placeholders.
- `frontend/`: React dashboard and API helper reserved for later integration.
- `architecture/`: future architecture diagrams.
- `screenshots/`: future application screenshots.
- `docs/`: future project documentation.

## Local development

Run commands from `cloudvault-aws/`. No database or AWS account is required.

### Backend (Windows PowerShell)

```powershell
Copy-Item .env.example .env
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Backend (macOS / Linux)

```sh
cp .env.example .env
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Visit http://localhost:8000/health or http://localhost:8000/docs.
The project-root `.env` is loaded independently of the working directory; environment variables take precedence. All three settings may remain blank for this phase.

### Frontend

Open a second terminal, starting at `cloudvault-aws/`:

```sh
cd frontend
npm ci
npm run dev
```

Visit the local URL shown by Vite (normally http://localhost:5173).

On Windows PowerShell, use `npm.cmd` instead of `npm` if script execution policy blocks `npm.ps1`.

Build and preview:

```sh
npm run build
npm run preview
```

The helper in `frontend/src/api/client.js` targets `http://localhost:8000` and is reserved for later integration. The dashboard makes no API calls. Configure a local proxy or explicitly scoped CORS when browser integration is added.

## Configuration

| Variable | Purpose | Required now |
| --- | --- | --- |
| `DATABASE_URL` | Future PostgreSQL connection URL | No |
| `AWS_REGION` | Future AWS region | No |
| `S3_BUCKET_NAME` | Future private document bucket | No |

Models, schemas, database setup, and service modules are docstring-only placeholders. They do not create engines, AWS clients, tables, buckets, or connections.

## Security

Credentials and secrets must never be committed. Keep local values in the ignored `.env` file; `.env.example` contains blank values only. A database URL may contain credentials and must be treated as a secret. Future EC2 access should use an IAM role instead of embedded AWS keys.

This foundation has no authentication and is intended for local development. The project title describes the planned application; production security controls are future work.
