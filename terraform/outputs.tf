output "public_ip" {
  value = aws_instance.prison_backend.public_ip
}

output "public_dns" {
  value = aws_instance.prison_backend.public_dns
}
