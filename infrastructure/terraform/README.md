# CloudVault Terraform — Phases 1 and 2

Infrastructure code for review only. **No apply has been executed and no AWS
resources have been created by this work.** CloudVault has not been deployed.

## Intended architecture

```text
Internet
    |
Internet Gateway
    |
Public subnet
    |
EC2 / FastAPI (application deployment is a later phase)
   |       |
   |       +--> private S3 bucket (IAM-controlled access)
   |
   +--> RDS PostgreSQL
        private subnet group spanning two AZs
        one active DB instance, single-AZ
```

Phase 1 networking, S3, security groups, and bucket-scoped IAM remain intact.
Phase 2 adds one EC2 instance, one DB subnet group, one RDS instance, and one
SSM managed-policy attachment (four additional managed resources).

## Region and Availability Zones

The provider uses `var.aws_region`, which is required and supplied by your
ignored `terraform.tfvars`. This project's intended region is **ap-south-2
(Asia Pacific — Hyderabad)**. There is no fallback region. The example also
uses ap-south-2. Existing terraform.tfvars values are preserved.

Two standard AZs are selected dynamically from the configured region.
The public subnet and private subnet A use the first sorted AZ; private subnet B
uses the second. No AMI ID or AZ name is hardcoded.

## EC2

- Configurable `ec2_instance_type`, default `t3.micro`, x86_64 T3/T3a family.
- Current Amazon Linux 2023 x86_64 AMI from the region's public SSM parameter.
- Public subnet, public IPv4, existing EC2 security group and IAM instance profile.
- 8 GiB encrypted gp3 root disk, removed with the instance; IMDSv2 required.
- Standard CPU credits to avoid surplus EC2 CPU-credit charges.
- User data only updates packages, installs Python/pip/Git, creates
  /opt/cloudvault, and enables the bundled SSM agent.
- No application clone, secrets, database connection string, reverse proxy,
  TLS certificate, service unit, or full deployment is installed.
- AMI/user-data updates can replace the instance; review future plans.

The existing role receives AmazonSSMManagedInstanceCore for management.
SSM uses outbound internet connectivity from this public host; no NAT or
paid VPC endpoints are added. Operators still need their own authorized
SSM permissions. A key pair is optional; `key_name = null` works with SSM.
SSH ingress stays disabled unless `allowed_ssh_cidr` is set to one IPv4 /32.
For SSH, supply an existing key pair in the configured region as well.

The AL2023 package Python is only machine preparation. Select and validate the
application's Python runtime during deployment; this phase does not promise
that the local application's full runtime requirements are installed.

## RDS

- PostgreSQL release queried through `aws_rds_engine_version`: the configured
  region's default available release, using its full version value.
- `db.t4g.micro` by default, configurable; 20 GiB encrypted gp3 storage.
- Private DB subnet group includes both private subnets.
- `publicly_accessible = false`, `multi_az = false`, PostgreSQL port 5432.
- Only the existing EC2 security group may connect to the RDS security group.
- One-day automated backup retention, minor upgrades enabled, major upgrades
  disabled, Extended Support enrollment disabled.
- No enhanced monitoring or Performance Insights.
- Demo teardown: deletion protection off, final snapshot skipped, automated
  backups deleted with the instance. Export needed data before any future teardown.

Two subnet-group AZs make placement possible but do not enable a Multi-AZ
standby. This deliberate single-AZ setup reduces demo cost and provides no
Multi-AZ failover. PostgreSQL's regional default can change; review the resolved
engine version and compatibility in each plan before applying. Confirm the
engine/class combination is orderable in Hyderabad before deployment.
Validation alone cannot establish regional availability.

## Security, state, and cost

S3 remains private with Block Public Access, disabled ACLs, SSE-S3 encryption,
and an HTTPS-only policy. IAM document permissions remain restricted to this
bucket. The new SSM managed policy grants management permissions, not broad S3
access. S3 resides outside the VPC subnets.

Only HTTP/HTTPS ingress is globally open to EC2. Port 8000 remains closed.
RDS has no public endpoint access or globally open PostgreSQL rule.
EC2 egress supports S3, SSM, package updates, and database connections.
Private route tables have no default internet route.

`db_password` is required and sensitive, with no default and no password output.
Sensitive marking redacts normal CLI output; **the password is still stored in
local Terraform state and saved plans**. Keep state secure and backed up.
Never commit real passwords, keys, terraform.tfvars, state, or plan files.
The existing ignore rules cover them; .terraform.lock.hcl stays trackable.
The example password is deliberately rejected until replaced privately.
Create a limited application database role during the later deployment phase;
the configured username is the RDS administrator.

No NAT Gateway, load balancer, extra instance, DNS service, CDN, cluster, cache,
remote-state bucket, or paid monitoring is added. Versioning stays suspended for
the demo, so S3 has no version-based recovery. RDS burstable CPU usage, compute,
storage, backups, data transfer, and public IPv4 can incur charges.

**Free-tier eligibility depends on your account and current AWS rules; these
instance sizes do not guarantee a free deployment.** Review
[AWS RDS free-tier details](https://aws.amazon.com/rds/free/) and
[public IPv4 pricing](https://aws.amazon.com/vpc/pricing/) before applying.

## Variables to configure

Keep existing network/S3 values in terraform.tfvars. Add or review:

```hcl
aws_region        = "ap-south-2"
db_name           = "cloudvault"
db_username       = "cloudvault_admin"
db_instance_class = "db.t4g.micro"
ec2_instance_type = "t3.micro"
key_name          = null
allowed_ssh_cidr  = null
```

Supply `db_password` privately in that ignored file or through
`TF_VAR_db_password`. Use 16–128 printable ASCII characters without spaces,
/, @, or double quotes. Never put a real password in the example or source.

Existing optional inputs: project_name (CloudVault), VPC CIDR (10.0.0.0/16),
public subnet (10.0.1.0/24), private subnets (10.0.2.0/24 and 10.0.3.0/24),
and s3_bucket_name (null generates a unique name). Changed subnet CIDRs must
be non-overlapping and contained in the VPC.

## Initialize, validate, and plan

Terraform >= 1.5 and < 2.0; AWS provider major version 6.
Run from infrastructure/terraform in PowerShell. Preserve the existing
terraform.tfvars; copy the example only if creating a new local configuration.

```powershell
terraform init
terraform fmt
terraform validate
# After configuring an authorized AWS profile and supplying db_password:
terraform plan
```

A local verified Terraform binary is also available at the project root:

```powershell
cd C:\Projects\cloudvault\cloudvault-aws\infrastructure\terraform
..\..\.terraform-tools\terraform.exe fmt -check
..\..\.terraform-tools\terraform.exe validate
..\..\.terraform-tools\terraform.exe plan
```

If you need Terraform on PATH, download the official Windows binary from
[HashiCorp](https://developer.hashicorp.com/terraform/install#windows), verify its
checksum, extract it to C:\Tools\Terraform, and add that directory to your user
PATH. Configure AWS credentials through the normal CLI/SSO credential chain;
nothing here embeds credentials or overrides the tfvars region.

Plan requires authenticated regional API reads for AZs, the SSM AMI parameter,
EC2 type information, and PostgreSQL versions. Review actual resource counts,
instance availability, cost, replacement actions, and resolved versions.

**DO NOT run terraform apply until the infrastructure plan has been reviewed.**
A future approved deployment may use `terraform plan -out=phase2.tfplan`,
`terraform show phase2.tfplan`, then `terraform apply phase2.tfplan`.
A saved plan applies without another confirmation. No apply was run here.

Future teardown only after explicit authorization: `terraform plan -destroy`
then `terraform destroy`. RDS deletion loses data under these demo settings.
S3 force_destroy remains false; a nonempty bucket blocks bucket deletion.
No destroy was run here.

## Outputs and validation results

Outputs include Phase 1 IDs plus EC2 ID/public IP/public DNS, RDS endpoint
(host:port), RDS port, and database name. These are connection coordinates,
not credentials. There is no database password or connection-URL output.

Terraform fmt, fmt -check, and validate passed with the installed AWS provider.
No AWS credentials/profile configuration was detected in this environment, so
an authenticated plan was not run. Regional AMI resolution, PostgreSQL version,
instance availability, and a full plan resource count remain unverified.
No resources were created, and no application code was changed.
