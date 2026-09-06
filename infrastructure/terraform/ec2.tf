data "aws_ssm_parameter" "amazon_linux" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "aws_ec2_instance_type" "application" {
  instance_type = var.ec2_instance_type
}

resource "aws_instance" "application" {
  ami                         = nonsensitive(data.aws_ssm_parameter.amazon_linux.value)
  instance_type               = var.ec2_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.ec2.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  associate_public_ip_address = true
  key_name                    = var.key_name
  monitoring                  = false
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    encrypted             = true
    delete_on_termination = true
  }

  credit_specification {
    cpu_credits = "standard"
  }

  user_data = <<-SCRIPT
    #!/bin/bash
    set -euo pipefail
    dnf upgrade -y
    dnf install -y python3 python3-pip git
    install -d -o ec2-user -g ec2-user -m 0755 /opt/cloudvault
    systemctl enable --now amazon-ssm-agent
  SCRIPT

  lifecycle {
    precondition {
      condition     = contains(data.aws_ec2_instance_type.application.supported_architectures, "x86_64")
      error_message = "Choose an x86_64 instance type compatible with the Amazon Linux AMI."
    }
  }

  depends_on = [
    aws_route.public_internet,
    aws_route_table_association.public,
    aws_vpc_security_group_egress_rule.ec2,
    aws_iam_role_policy_attachment.ssm
  ]

  tags = { Name = "${local.name}-ec2" }
}

# SSM management without opening SSH or adding VPC endpoints.
data "aws_partition" "current" {}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
