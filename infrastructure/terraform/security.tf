resource "aws_security_group" "ec2" {
  name        = "${local.name}-ec2-sg"
  description = "Future web host; SSH is optional and restricted to one administrator IP."
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "${local.name}-ec2-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.ec2.id
  description       = "Future public HTTP endpoint"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  count             = var.allowed_ssh_cidr == null ? 0 : 1
  security_group_id = aws_security_group.ec2.id
  description       = "SSH from the administrator IP only"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = var.allowed_ssh_cidr
}

resource "aws_vpc_security_group_egress_rule" "ec2" {
  security_group_id = aws_security_group.ec2.id
  description       = "Future host updates, S3 access, and database connections"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-rds-sg"
  description = "Future PostgreSQL access from the CloudVault EC2 security group only."
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "${local.name}-rds-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "postgresql" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.ec2.id
  description                  = "PostgreSQL from the future application host"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

# No RDS egress rule is needed for stateful replies to incoming connections.
# Port 8000 is not publicly exposed; a reverse proxy belongs to Phase 2.
