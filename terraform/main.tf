terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
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


# --- Latest Amazon Linux 2023 AMI (x86_64) --- CHANGING TO ARM64 to fit 1cpu limit
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    # This broader filter is more reliable for AL2023
    values = ["al2023-ami-2023*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# --- Security Group ---
resource "aws_security_group" "app_sg" {
  name_prefix = "web-server-sg-" #Bypass the duplicate error
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

# 1. Tell Terraform to create/register the key in whatever region we are in
resource "aws_key_pair" "deployer" {
  key_name   = "devina-myfitness-tf" # Giving it a slightly different name to avoid conflict
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDFLuMWIUUH4bhkFR5kiwfEbn/AUPj/oR2ZjhFE0xVNnTOrUG8/z23FnVwh1+rjpoKHoCGAhr2atjS5UbjbfrUdos64888LSx80zCDeyaLdgXUMKl5HPRQ1kGYCaPX885yQbwGtGV5dcI8DExACOgo9npgxl3fuo9uaBKR9AvpT/Yd1NBbsg1je3/Ukap0a29awe3gxyWmi0sgwsNmZDBCb4HRLfDOtjOnumxgWRY+POgMQgQnLygdkn13xsyM8KyOoEQWYhSAZXnxIiLreM8LGjx5CSciuWORPHBGKuy9awo9n5HFTH88BYkcy+HmXBW1DIU99Aa+RDBtG1ucrufAv
  "

# --- EC2 Instance ---
resource "aws_instance" "prison_backend" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro" #
  subnet_id = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  key_name = "aws_key_pair.deployer.key_name"   # Must exist in your AWS account

  # --- NEW: bootstrap script ---
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Update and install dependencies
    dnf update -y
    dnf install -y python3 python3-pip openssl

    # Setup directory (Matched to your CI/CD path)
    mkdir -p /home/ec2-user/my-fitness-app/certs
    cd /home/ec2-user/my-fitness-app/certs

    # Generate SSL Certs
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout devina.key -out devina.crt \
      -subj "/C=GB/ST=GreaterManchester/L=Manchester/O=Devina/OU=DevOps/CN=localhost"
    chmod 600 devina.key devina.crt

    # Create the Flask app file
    cat > /home/ec2-user/my-fitness-app/app.py << 'APP'
from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from HTTPS Flask on EC2!"

if __name__ == "__main__":
    # Point to the certs folder created above
    app.run(host="0.0.0.0", port=5000, ssl_context=("certs/devina.crt", "certs/devina.key"))
APP

    # Setup Virtual Environment and Flask
    cd /home/ec2-user/my-fitness-app
    python3 -m venv venv
    ./venv/bin/pip install flask

    # CREATE SYSTEMD SERVICE (This makes 'systemctl restart' work)
    cat > /etc/systemd/system/flask.service << 'SERVICE'
[Unit]
Description=Flask app
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/my-fitness-app
# Using the venv path ensures all dependencies are found
ExecStart=/home/ec2-user/my-fitness-app/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

    # Start the service
    systemctl daemon-reload
    systemctl enable flask
    systemctl start flask

    # Fix permissions
    chown -R ec2-user:ec2-user /home/ec2-user/my-fitness-app
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
