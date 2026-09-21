# CloudVault

CloudVault is a small document management application deployed on AWS for a university cloud computing assignment. A React frontend uses a FastAPI API to upload, list, download, and delete documents. PostgreSQL stores metadata; the selected storage backend holds file contents.

## Assignment objective

Design and deploy a cloud application using a VPC, public and private networks, EC2, RDS, and S3, with secure communication between the application, database, and storage layers.

## Key features

- Upload one document at a time, up to 10 MiB; reject empty files and invalid filenames.
- List documents newest first, view metadata, download files, and delete documents.
- Store metadata in PostgreSQL and file contents in local storage or private S3.
- Check database and storage availability through `/health`.

## Architecture

```text
Internet / browser
        |
        v
EC2 in public subnet (port 80)
  Nginx serves React and proxies /api and /health
        |
        v
  FastAPI / Uvicorn (127.0.0.1:8000, managed by systemd)
        |                               |
        v                               v
RDS PostgreSQL                    Private S3 bucket
in two private subnets            accessed through EC2 IAM role
```

Terraform provisions a custom VPC, Internet Gateway, public and private route tables, one public EC2 subnet, and two private subnets for the RDS DB subnet group. EC2 has a public address. RDS has `publicly_accessible = false`; its security group permits TCP 5432 only from the EC2 security group. The S3 bucket has Block Public Access enabled. FastAPI is reachable through Nginx and is not exposed directly on port 8000.

## AWS services used

| Service | Purpose |
| --- | --- |
| VPC and subnets | Separate the public application host from the private database |
| EC2 | Host Nginx, React, and FastAPI |
| RDS PostgreSQL | Store document metadata |
| S3 | Store uploaded documents privately |
| IAM | Give EC2 bucket-scoped S3 permissions through an instance profile |
| Security Groups | Restrict inbound web and database traffic |
| Systems Manager Session Manager | Access EC2 without opening the application port or storing an SSH key in the repository |

## Security design

EC2 uses its IAM role for S3 access; no AWS access keys are stored on the instance or in the repository. S3 Block Public Access, server-side encryption, and an HTTPS-only bucket policy are defined in Terraform. RDS is private and accepts PostgreSQL traffic only from the EC2 security group. The application binds to loopback behind Nginx. Credentials belong in ignored local configuration or a restricted EC2 environment file, never in tracked files.

The current public web endpoint uses **HTTP on port 80**. It does not provide HTTPS or application-level authentication. Use dummy documents only; see [Known limitations](#known-limitations).

## Technology stack

- Frontend: React 19 and Vite 8 (Node.js 22.12+ for builds).
- Backend: Python, FastAPI, Uvicorn, SQLAlchemy 2, psycopg, and boto3.
- Deployment: Amazon Linux 2023, Nginx, systemd, Terraform, AWS CLI, and SSM.

## Repository structure

```text
backend/                  FastAPI app, database model, storage backends, tests
frontend/                 React dashboard, API client, Vite build
infrastructure/terraform/ VPC, EC2, RDS, S3, IAM, and security groups
deployment/               Nginx and systemd configuration templates
docs/ architecture/ screenshots/  Assignment documentation folders
```

## Local development

Local mode requires PostgreSQL and stores files under `backend/storage/documents/`. Create a PostgreSQL role and database using your own credentials, then copy `.env.example` to the project-root `.env` and set `DATABASE_URL` and `STORAGE_BACKEND=local`. The `.env` file is ignored by Git. The URL in `.env.example` is a placeholder; URL-encode special characters in your own password.

From the project root in PowerShell:

```powershell
Copy-Item .env.example .env
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, from `frontend/`:

```powershell
npm.cmd ci
npm.cmd run dev -- --port 5173 --strictPort
```

Open `http://localhost:5173`. Vite proxies `/api` to the local backend. The backend allows that local origin through CORS. Startup creates missing tables; it does not migrate existing schemas.

## AWS deployment overview

Terraform provisions the infrastructure. The application runs on EC2: Nginx serves the Vite production build and proxies `/api` and `/health` to Uvicorn, which systemd keeps running on `127.0.0.1:8000`. In AWS mode, FastAPI connects to private RDS PostgreSQL and uses boto3 with the EC2 instance profile to access private S3. AWS CLI was used for verification and SSM Session Manager for EC2 access. See [deployment](deployment/README.md) and [Terraform](infrastructure/terraform/README.md) for the repository configuration.

## Environment variables

| Variable | Local mode | AWS mode |
| --- | --- | --- |
| `DATABASE_URL` | Local `postgresql+psycopg` connection URL | Private RDS `postgresql+psycopg` connection URL |
| `STORAGE_BACKEND` | `local` (default) | `s3` |
| `AWS_REGION` | Leave blank | AWS deployment region |
| `S3_BUCKET_NAME` | Leave blank | Private document bucket name |

Only placeholders belong in `.env.example`. The frontend normally uses same-origin `/api`; `VITE_API_BASE_URL` can override its API origin when needed.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Check database and selected storage; return 503 if unavailable |
| POST | `/api/documents` | Upload a file in multipart field `file` |
| GET | `/api/documents` | List document metadata |
| GET | `/api/documents/{id}` | Get one document's metadata |
| GET | `/api/documents/{id}/download` | Stream a private file as an attachment |
| DELETE | `/api/documents/{id}` | Delete the document and its stored file |

## Testing

From `backend/`, run `.venv/Scripts/python.exe -m pytest -q`. On Windows, if pytest cannot write its default temporary directory, use `-p no:cacheprovider --basetemp=.pytest-temp-final`. The suite currently passes **27 tests**. It uses SQLite and mocked S3 interactions; it does not replace live RDS or IAM verification. From `frontend/`, `npm.cmd run build` passes. `terraform fmt -check` and `terraform validate` pass with the project-local Terraform binary.

## Terraform workflow

The infrastructure code is in `infrastructure/terraform/`. Its variables and outputs describe the VPC, EC2, RDS, S3, IAM, and security groups. Review `terraform plan` before any future infrastructure change. Keep local `.tfvars`, state, and saved plans out of Git. Terraform provisions infrastructure; application installation and service setup are separate EC2 deployment steps.

## Verification and evidence

The deployed `/health` response was `{"status":"healthy","database":"connected","storage":"available"}`. Upload, list, download, and delete were verified through the deployed UI. AWS CLI checks confirmed the private RDS configuration, S3 Block Public Access, security group rule, and instance profile. Assignment diagrams and screenshots can be added under `architecture/`, `docs/`, and `screenshots/` later.

## Known limitations

- The web endpoint is HTTP only and the application has no user authentication. Use dummy/demo documents and limit access to assignment use.
- RDS and S3 changes cannot form one distributed atomic transaction; failures or crashes may require reconciliation.
- The RDS instance is single-AZ. Startup creates missing tables but does not perform schema migrations.

## Cleanup

Stop and destroy demo resources after the assignment to avoid unnecessary AWS charges. The S3 bucket has `force_destroy = false`, so remove its objects before a planned `terraform destroy`; export any data that must be kept first. Review the destroy plan because the demo RDS settings do not retain a final snapshot.

## Future improvements

Add HTTPS, user authentication, schema migrations, and automated reconciliation between PostgreSQL metadata and S3 objects before using real documents.
