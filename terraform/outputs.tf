output "application_url" {
  description = "URL pública da aplicação."
  value       = "http://${aws_lb.app.dns_name}"
}

output "alb_dns_name" {
  value = aws_lb.app.dns_name
}

output "redis_private_ip" {
  value = aws_instance.redis.private_ip
}

output "autoscaling_group_name" {
  value = aws_autoscaling_group.app.name
}

output "ecr_image" {
  value = local.app_image
}

output "ecr_repository_url" {
  description = "URL do repositório ECR criado pelo Terraform."
  value       = aws_ecr_repository.app.repository_url
}
