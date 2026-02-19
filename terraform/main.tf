variable "tunnel_token" {
  description = "Cloudflare Tunnel Token"
  type        = string
  sensitive   = true
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-2" # London
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

# --- Latest Amazon Linux 2023 AMI ---
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# --- Security Group ---
resource "aws_security_group" "app_sg" {
  name_prefix = "web-server-sg-"
  description = "Allow inbound traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "t3.micro"
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  key_name               = "devina-myfitness"

  user_data = <<EOF
#!/bin/bash
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting setup..."
dnf update -y
dnf install -y python3 python3-pip openssl git

# Install Cloudflared
curl -L --output /tmp/cloudflared.rpm https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
dnf install -y /tmp/cloudflared.rpm

# Install Cloudflared Service
cloudflared service install ${var.tunnel_token}

# Setup App Directory
mkdir -p /home/ec2-user/my-fitness-app
cd /home/ec2-user/my-fitness-app

# Setup Python Venv
python3 -m venv venv
./venv/bin/pip install flask

# Create the service file
cat <<SERVICE > /etc/systemd/system/flask.service
[Unit]
Description=Flask app
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/my-fitness-app/backend
# Change app.py to ./app.py or the full path to be safe:
ExecStart=/home/ec2-user/my-fitness-app/venv/bin/python /home/ec2-user/my-fitness-app/backend/app.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable flask
systemctl start flask
systemctl enable cloudflared
systemctl start cloudflared

chown -R ec2-user:ec2-user /home/ec2-user/my-fitness-app
echo "Setup complete!"
EOF

  tags = {
    Name = "PrisonProjectBackend"
  }
}

# --- Elastic IP ---
resource "aws_eip" "backend_eip" {
  instance = aws_instance.prison_backend.id
  domain   = "vpc"

  tags = {
    Name = "PrisonProjectEIP"
  }
}

# --- Outputs
output "static_public_ip" {
  description = "The public IP of the Elastic IP"
  value       = aws_eip.backend_eip.public_ip
}

output "ec2_id" {
  value = aws_instance.prison_backend.id
}