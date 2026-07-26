provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      Owner       = var.owner
      Purpose     = "minicurso-cloud"
      ManagedBy   = "terraform"
    }
  }
}
