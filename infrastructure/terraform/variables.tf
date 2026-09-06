variable "aws_region" {
  description = "AWS region for the future infrastructure."
  type        = string
}

variable "project_name" {
  description = "Project tag; resource names use its lowercase form."
  type        = string
  default     = "CloudVault"

  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9-]{0,29}$", var.project_name))
    error_message = "Use 1-30 letters, digits, or hyphens, starting with a letter."
  }
}

variable "vpc_cidr" {
  description = "IPv4 CIDR for the VPC; subnets must fit within it without overlap."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "IPv4 CIDR for the public subnet."
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_a_cidr" {
  description = "IPv4 CIDR for the first private subnet."
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_b_cidr" {
  description = "IPv4 CIDR for the second private subnet in another AZ."
  type        = string
  default     = "10.0.3.0/24"
}

variable "allowed_ssh_cidr" {
  description = "Optional administrator public IPv4 /32. Null disables SSH ingress."
  type        = string
  default     = null

  validation {
    condition = var.allowed_ssh_cidr == null ? true : (
      can(cidrnetmask(var.allowed_ssh_cidr)) &&
      can(regex("/32$", var.allowed_ssh_cidr)) &&
      var.allowed_ssh_cidr != "0.0.0.0/32"
    )
    error_message = "Use a single administrator IPv4 address with /32, or null to disable SSH."
  }
}

variable "s3_bucket_name" {
  description = "Optional globally unique bucket name. Null uses an AWS-provider-generated unique name."
  type        = string
  default     = null

  validation {
    condition = var.s3_bucket_name == null ? true : (
      length(var.s3_bucket_name) >= 3 &&
      length(var.s3_bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.s3_bucket_name))
    )
    error_message = "Use null or a 3-63 character lowercase bucket name with digits/hyphens; AWS reserved-name restrictions also apply."
  }
}

variable "db_name" {
  description = "Initial PostgreSQL database name."
  type        = string
  default     = "cloudvault"

  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9]{0,62}$", var.db_name))
    error_message = "Use 1-63 alphanumeric characters, starting with a letter."
  }
}

variable "db_username" {
  description = "RDS administrator username; use a separate limited application role during deployment."
  type        = string
  default     = "cloudvault_admin"

  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9_]{0,15}$", var.db_username))
    error_message = "Use 1-16 letters, digits, or underscores, starting with a letter."
  }
}

variable "db_password" {
  description = "RDS administrator password. Supply privately; Terraform state still contains this sensitive value."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition = (
      length(var.db_password) >= 16 &&
      length(var.db_password) <= 128 &&
      can(regex("^[!-~]+$", var.db_password)) &&
      length(regexall("[/@\"]", var.db_password)) == 0 &&
      var.db_password != "REPLACE_WITH_A_PRIVATE_PASSWORD"
    )
    error_message = "Use 16-128 printable ASCII characters without spaces, /, @, or double quotes; replace the example placeholder."
  }
}

variable "db_instance_class" {
  description = "Small RDS class; regional availability and free-tier eligibility must be verified."
  type        = string
  default     = "db.t4g.micro"
}

variable "ec2_instance_type" {
  description = "x86_64 burstable T3/T3a size. Standard credits avoid surplus CPU credit charges."
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t3a?\\.", var.ec2_instance_type))
    error_message = "Choose an x86_64 t3 or t3a instance type."
  }
}

variable "key_name" {
  description = "Optional existing EC2 key pair in the configured region; null uses SSM without SSH."
  type        = string
  default     = null
}
