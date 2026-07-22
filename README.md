# Cloud Black Friday Demo

Aplicação demonstrativa desenvolvida para um minicurso de **Computação em Nuvem**, com foco em elasticidade, escalabilidade horizontal, balanceamento de carga e containers na AWS.

A solução simula um cenário de alta demanda durante uma Black Friday. A aplicação gera carga real de CPU e permite acompanhar o Auto Scaling adicionando novas instâncias EC2, enquanto o Application Load Balancer distribui as requisições entre os servidores disponíveis.

## Arquitetura

```text
Usuário
   │
   ▼
Application Load Balancer
   │
   ▼
Target Group
   │
   ▼
Auto Scaling Group
   │
   ├───────────────┐
   ▼               ▼
EC2 + Docker   EC2 + Docker
Flask App      Flask App
   │               │
   └───────┬───────┘
           ▼
     Redis compartilhado

CloudWatch
   │
   ▼
Auto Scaling por CPU
```

## Tecnologias

- Python 3.12
- Flask
- Gunicorn
- Redis
- Docker e Docker Compose
- HTML, CSS e JavaScript
- Amazon EC2
- EC2 Auto Scaling
- Application Load Balancer
- Amazon ECR
- Amazon CloudWatch
- AWS IAM e Systems Manager

## Funcionalidades

- simulação de Black Friday;
- contagem regressiva do evento;
- geração controlada de carga;
- consumo real de CPU;
- CPU dos servidores em tempo real;
- usuários ativos;
- requisições registradas nos últimos 30 segundos;
- tempo médio de resposta;
- identificação do servidor que respondeu;
- exibição do IP privado;
- nomes amigáveis como `Servidor Web 1` e `Servidor Web 2`;
- estado compartilhado entre instâncias utilizando Redis;
- scale-out e scale-in automáticos;
- distribuição de tráfego pelo ALB.

## Auto Scaling

A política utiliza Target Tracking com base na média de CPU do Auto Scaling Group.

| Configuração | Valor |
|---|---:|
| Métrica | ASGAverageCPUUtilization |
| Target | 50% |
| Capacidade mínima | 1 |
| Capacidade máxima | 3 |
| Instance warmup | 45 segundos |

O scale-in é mais conservador que o scale-out para evitar a remoção prematura de capacidade.

## Execução local

### Pré-requisitos

- Git
- Docker
- Docker Compose

Clone o projeto:

```bash
git clone https://github.com/aryaneandrade/cloud-black-friday-demo.git
cd cloud-black-friday-demo
```

Inicie os containers:

```bash
docker compose up --build -d
```

Verifique os serviços:

```bash
docker compose ps
```

Acesse:

```text
http://localhost:8080
```

Teste os endpoints:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/status
```

Para encerrar:

```bash
docker compose down
```

## Estrutura do projeto

```text
cloud-black-friday-demo/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── data/
│   └── store.json
├── static/
│   ├── app.js
│   └── style.css
├── templates/
│   └── index.html
└── README.md
```

## Objetivos de aprendizagem

O projeto demonstra de forma prática:

- elasticidade;
- escalabilidade horizontal;
- alta disponibilidade;
- balanceamento de carga;
- containers;
- monitoramento;
- Auto Scaling;
- arquiteturas distribuídas.

## Melhorias futuras

- HTTPS com AWS Certificate Manager;
- domínio com Amazon Route 53;
- Redis gerenciado com Amazon ElastiCache;
- infraestrutura como código;
- pipeline de CI/CD;
- logs centralizados;
- testes automatizados.

## Versão

`v1.2.3`

## Autora

**Aryane Andrade**

Projeto desenvolvido para fins acadêmicos e demonstração de conceitos de Computação em Nuvem.