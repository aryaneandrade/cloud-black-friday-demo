variable "aws_region" {
  description = "Região AWS."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome-base dos recursos."
  type        = string
  default     = "cloud-black-friday-demo"
}

variable "environment" {
  description = "Ambiente."
  type        = string
  default     = "demo"
}

variable "owner" {
  description = "Responsável pelo projeto."
  type        = string
  default     = "Aryane"
}

variable "vpc_id" {
  description = "VPC padrão usada pelo projeto."
  type        = string
  default     = "vpc-06c9c96e4f5e213ec"
}

variable "subnet_ids" {
  description = "Sub-redes públicas usadas pelo ALB e Auto Scaling Group."
  type        = list(string)
  default = [
    "subnet-035b85288b2f79876",
    "subnet-0d837f4dc8070c243",
    "subnet-0e82804de2118f70a"
  ]
}

variable "redis_subnet_id" {
  description = "Sub-rede da EC2 fixa do Redis."
  type        = string
  default     = "subnet-0e82804de2118f70a"
}

variable "ami_id" {
  description = "AMI Amazon Linux 2023 usada atualmente."
  type        = string
  default     = "ami-01edba92f9036f76e"
}

variable "instance_type" {
  description = "Tipo das instâncias da aplicação e do Redis."
  type        = string
  default     = "t3.micro"
}

variable "ecr_repository_name" {
  description = "Repositório ECR existente, preservado fora deste Terraform."
  type        = string
  default     = "cloud-black-friday-demo"
}

variable "image_tag" {
  description = "Tag fixa da imagem da aplicação."
  type        = string
  default     = "v1.2.3"
}

variable "app_port" {
  description = "Porta da aplicação Flask."
  type        = number
  default     = 8080
}

variable "redis_port" {
  description = "Porta do Redis."
  type        = number
  default     = 6379
}

variable "asg_min_size" {
  type    = number
  default = 1
}

variable "asg_desired_capacity" {
  type    = number
  default = 1
}

variable "asg_max_size" {
  type    = number
  default = 3
}

variable "cpu_target_value" {
  description = "CPU média alvo da política Target Tracking."
  type        = number
  default     = 50
}
