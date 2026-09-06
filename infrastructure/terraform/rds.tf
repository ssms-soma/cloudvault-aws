# Query the region's default currently available PostgreSQL release at plan time.
data "aws_rds_engine_version" "postgresql" {
  engine = "postgres"
}

resource "aws_db_subnet_group" "documents" {
  name       = "${local.name}-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  tags       = { Name = "${local.name}-db-subnet-group" }
}

resource "aws_db_instance" "documents" {
  identifier                   = "${local.name}-postgres"
  engine                       = "postgres"
  engine_version               = data.aws_rds_engine_version.postgresql.version_actual
  instance_class               = var.db_instance_class
  db_name                      = var.db_name
  username                     = var.db_username
  password                     = var.db_password
  port                         = 5432
  db_subnet_group_name         = aws_db_subnet_group.documents.name
  vpc_security_group_ids       = [aws_security_group.rds.id]
  publicly_accessible          = false
  multi_az                     = false
  allocated_storage            = 20
  storage_type                 = "gp3"
  storage_encrypted            = true
  backup_retention_period      = 1
  deletion_protection          = false
  skip_final_snapshot          = true
  delete_automated_backups     = true
  auto_minor_version_upgrade   = true
  allow_major_version_upgrade  = false
  monitoring_interval          = 0
  performance_insights_enabled = false
  engine_lifecycle_support     = "open-source-rds-extended-support-disabled"
  copy_tags_to_snapshot        = true

  tags = { Name = "${local.name}-postgres" }
}
