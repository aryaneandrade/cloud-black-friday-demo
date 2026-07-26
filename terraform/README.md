# Terraform — Cloud Black Friday Demo

Recria a infraestrutura da demonstração:

- ALB público em HTTP/80
- Target Group HTTP/8080 com health check `/health`
- Auto Scaling Group 1/1/3
- Target Tracking em 50% de CPU
- EC2 fixa para Redis em Docker
- EC2 da aplicação em Docker usando a imagem ECR `v1.2.3`
- VPC padrão e três sub-redes públicas existentes
- Security Groups separados para ALB, aplicação e Redis
- IAM Role com SSM e ECR Pull Only

O ECR é consultado por data source e não é destruído por este Terraform.

## Validar

```bash
terraform init
terraform fmt -recursive
terraform validate
```

Não execute `terraform apply` enquanto os recursos manuais com os mesmos nomes ainda existirem.

## Recriar depois

```bash
cp terraform.tfvars.example terraform.tfvars
terraform plan
terraform apply
terraform output application_url
```

## Remover

```bash
terraform destroy
```
