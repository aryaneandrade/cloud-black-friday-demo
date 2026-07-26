locals {
  name = var.project_name

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner
    Purpose     = "minicurso-cloud"
    ManagedBy   = "terraform"
  }

  app_image = "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
}
