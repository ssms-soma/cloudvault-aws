output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "private_subnet_a_id" {
  description = "First private subnet ID"
  value       = aws_subnet.private_a.id
}

output "private_subnet_b_id" {
  description = "Second private subnet ID"
  value       = aws_subnet.private_b.id
}

output "ec2_security_group_id" {
  description = "Future EC2 security group ID"
  value       = aws_security_group.ec2.id
}

output "rds_security_group_id" {
  description = "Future RDS security group ID"
  value       = aws_security_group.rds.id
}

output "s3_bucket_name" {
  description = "Private document bucket name"
  value       = aws_s3_bucket.documents.id
}

output "ec2_iam_role_name" {
  description = "Future EC2 IAM role name"
  value       = aws_iam_role.ec2.name
}

output "ec2_instance_profile_name" {
  description = "Future EC2 instance profile name"
  value       = aws_iam_instance_profile.ec2.name
}

output "ec2_instance_id" {
  description = "ec2 instance id for the future deployment."
  value       = aws_instance.application.id
}

output "ec2_public_ip" {
  description = "ec2 public ip for the future deployment."
  value       = aws_instance.application.public_ip
}

output "ec2_public_dns" {
  description = "ec2 public dns for the future deployment."
  value       = aws_instance.application.public_dns
}

output "rds_endpoint" {
  description = "rds endpoint for the future deployment."
  value       = aws_db_instance.documents.endpoint
}

output "rds_port" {
  description = "rds port for the future deployment."
  value       = aws_db_instance.documents.port
}

output "database_name" {
  description = "database name for the future deployment."
  value       = aws_db_instance.documents.db_name
}
