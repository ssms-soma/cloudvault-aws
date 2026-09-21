# EC2 deployment configuration

These templates are used by the deployed application. EC2 reaches private RDS
on 5432 and private S3 through its instance profile. No static AWS keys are
needed. The steps below support rebuilding or updating the instance.

1. Build the frontend with `npm ci` and `npm run build` from `frontend/`.
   Leave `VITE_API_BASE_URL` unset for the same-origin `/api` proxy.
2. Transfer backend source, requirements, and `frontend/dist/` to
   `/opt/cloudvault/` on EC2. The current Terraform user data creates this
   directory but does not transfer or install the application.
3. Install a compatible Python runtime, create
   `/opt/cloudvault/backend/.venv`, and install `backend/requirements.txt`.
   Install Nginx. Confirm the AMI's package/runtime versions before use.
4. Provision a limited PostgreSQL application role with the rights needed for
   the current startup `create_all` check and document CRUD, or create the table
   with an administrator before starting the service. Place an EC2-only file at
   `/etc/cloudvault/backend.env` with `DATABASE_URL`, `STORAGE_BACKEND=s3`,
   `AWS_REGION`, and `S3_BUCKET_NAME`. Restrict file permissions to the service
   account and administrator. Keep this file out of Git, Terraform user data,
   shell history, and screenshots.
5. Install `cloudvault-api.service` under `/etc/systemd/system/` and
   `cloudvault.nginx.conf` under `/etc/nginx/conf.d/`. Enable and start both
   services after checking their configuration. Uvicorn binds to loopback;
   only Nginx accepts public HTTP traffic.
6. Verify `/health`, upload, list, download, and delete. Inspect RDS rows and
   S3 objects using authorized CLI commands. Capture redacted evidence.

The Nginx template listens on port 80. HTTPS is not configured; use a suitable
TLS setup before exposing private documents to real users. CloudVault has no
authentication or per-user ownership, so restrict access to a controlled demo
audience. The current `/health` path is reachable through Nginx and returns only
dependency status labels.
