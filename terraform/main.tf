terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1"
}

# --- Default VPC and Subnets ---
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}


# --- Latest Amazon Linux 2023 AMI (x86_64) ---
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# --- Security Group ---
resource "aws_security_group" "app_sg" {
  name        = "myfitness-app-sg"
  description = "Allow SSH and Flask app"
  vpc_id      = data.aws_vpc.default.id

  # SSH from your home IP ONLY
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["176.26.86.116/32"] # Your IP
  }

  # Flask app on port 5000 (public)
  ingress {
    description = "Flask app"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- EC2 Instance ---
resource "aws_instance" "prison_backend" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro" #Free tier
  subnet_id = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  key_name = "devina-key"   # Must exist in your AWS account

  tags = {
    Name = "PrisonProjectBackend"
  }
}

# --- Output ---
output "ec2_public_ip" {
  value = aws_instance.prison_backend.public_ip
}

output "ec2_public_dns" {
  value = aws_instance.prison_backend.public_dns
}
