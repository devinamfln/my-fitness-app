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
  name        = "web-server-sg"
  description = "Allow inbound traffic"
  vpc_id      = data.aws_vpc.default.id

  # Change from home IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # CHANGED FROM HOME IP
  }

  # Flask app on port 5000 (public)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
# adding connectivity
  ingress {
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
  key_name = "my-fitness-key"   # Must exist in your AWS account

  # --- NEW: bootstrap script ---
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Update packages
    dnf update -y

    # Install Python, pip and OpenSSL
    dnf install -y python3 python3-pip openssl

    # Create app directory
    mkdir -p /home/ec2-user/app/certs
    cd /home/ec2-user/app/certs

    # Generate self-signed certificate (valid 365 days)
    # Using CN=localhost just to avoid needing Terraform interpolation
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout devina.key -out devina.crt \
      -subj "/C=GB/ST=GreaterManchester/L=Manchester/O=Devina/OU=DevOps/CN=localhost"

    chmod 600 devina.key devina.crt

    # Create the Flask app
    cat > /home/ec2-user/app/app.py << 'APP'
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from HTTPS Flask on EC2!"

@app.route("/dashboard")
def dashboard():
    return "This is the dashboard over HTTPS."

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        ssl_context=("certs/devina.crt", "certs/devina.key")
    )
APP

    # Install Flask
    pip3 install flask

    # Fix permissions so ec2-user owns the app
    chown -R ec2-user:ec2-user /home/ec2-user/app

    # Start the app in the background
    cd /home/ec2-user/app
    sudo -u ec2-user nohup python3 app.py > app.log 2>&1 &
  EOF

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
