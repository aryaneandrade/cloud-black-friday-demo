# ☁️ Cloud Black Friday Demo

Aplicação demonstrativa desenvolvida para um minicurso de **Computação em Nuvem**, simulando um cenário de alta demanda durante uma Black Friday.

O projeto demonstra, na prática, conceitos de **elasticidade**, **escalabilidade horizontal**, **balanceamento de carga**, **containers** e **Infraestrutura como Código (IaC)** utilizando serviços da AWS.

---

## Arquitetura

```text
                     Usuário
                        │
                        ▼
          Application Load Balancer (ALB)
                        │
                        ▼
              Auto Scaling Group (EC2)
                 │               │
                 ▼               ▼
          Docker + Flask   Docker + Flask
                 │               │
                 └───────┬───────┘
                         ▼
                 Redis Compartilhado
```

---

## Tecnologias

- Python 3.12
- Flask
- Gunicorn
- Redis
- Docker
- Docker Compose
- Terraform
- Amazon EC2
- EC2 Auto Scaling
- Application Load Balancer (ALB)
- Amazon Elastic Container Registry (ECR)
- Amazon CloudWatch
- AWS IAM
- AWS Systems Manager (SSM)

---

## Funcionalidades

- Simulação de Black Friday
- Geração de carga real de CPU
- Escalabilidade horizontal automática
- Balanceamento de carga entre instâncias
- Estado compartilhado utilizando Redis
- Monitoramento em tempo real
- Deploy automatizado com Terraform
- Remoção completa da infraestrutura

---

## Infraestrutura

Toda a infraestrutura é provisionada utilizando **Terraform**.

Os principais recursos criados automaticamente são:

- Amazon ECR
- IAM Role e Instance Profile
- Security Groups
- EC2 (Redis)
- Launch Template
- Auto Scaling Group
- Application Load Balancer
- Target Group
- Listener HTTP
- Política de Auto Scaling

A VPC padrão da AWS é reutilizada.

---

## Execução Local

### Pré-requisitos

- Git
- Docker
- Docker Compose

Clone o projeto:

```bash
git clone https://github.com/aryaneandrade/cloud-black-friday-demo.git
cd cloud-black-friday-demo
```

Execute:

```bash
docker compose up --build -d
```

Acesse:

```text
http://localhost:8080
```

---

## Deploy na AWS

Após configurar suas credenciais da AWS, execute:

```bash
./deploy.sh
```

O script realiza automaticamente:

- Criação do Amazon ECR
- Build da imagem Docker
- Push da imagem para o ECR
- Provisionamento da infraestrutura com Terraform
- Validação da aplicação

---

## Remover a Infraestrutura

Para remover todos os recursos criados pelo projeto:

```bash
./destroy.sh
```

Serão removidos automaticamente:

- EC2
- Auto Scaling Group
- Load Balancer
- Launch Template
- Redis
- Security Groups
- IAM
- Amazon ECR

A VPC padrão da AWS não é removida.

---

## Estrutura do Projeto

```text
cloud-black-friday-demo/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── deploy.sh
├── destroy.sh
├── terraform/
├── static/
├── templates/
├── data/
├── requirements.txt
└── README.md
```

---

## Objetivos de Aprendizagem

Este projeto demonstra, na prática:

- Containers com Docker
- Elasticidade
- Escalabilidade Horizontal
- Auto Scaling
- Load Balancer
- Alta Disponibilidade
- Amazon ECR
- Terraform
- Infraestrutura como Código (IaC)

---

## Melhorias Futuras

- HTTPS com AWS Certificate Manager
- Amazon Route 53
- Amazon ElastiCache
- Pipeline CI/CD
- Logs centralizados
- Testes automatizados

---

## Versão

**v2.0.0**

---

## Autora

**Aryane Andrade**

Projeto desenvolvido para fins acadêmicos e demonstração prática de Computação em Nuvem utilizando AWS, Docker e Terraform.