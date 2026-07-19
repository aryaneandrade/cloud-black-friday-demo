# ☁️ Cloud Black Friday Demo

Uma demonstração interativa de Computação em Nuvem desenvolvida para fins educacionais.

O projeto simula um e-commerce durante a Black Friday, permitindo demonstrar conceitos fundamentais de Cloud Computing como escalabilidade, balanceamento de carga, Auto Scaling e alta disponibilidade utilizando uma interface moderna e interativa.

---

# 🎯 Objetivo

Este projeto foi criado para auxiliar estudantes de Tecnologia da Informação na compreensão dos principais conceitos de Computação em Nuvem através de uma demonstração prática.

Durante a apresentação é possível visualizar:

- Contagem regressiva para a Black Friday
- Mudança automática do tema da loja
- Alteração dinâmica dos preços
- Crescimento do número de usuários simultâneos
- Aumento da carga da aplicação
- Simulação de escalabilidade
- Mudança do servidor (EC2) atendendo o usuário
- Conceitos de Load Balancer e Auto Scaling

---

# 🖥 Demonstração

Fluxo da apresentação:

1. Loja em funcionamento normal
2. Início da Black Friday
3. Contagem regressiva
4. Mudança visual completa
5. Início da carga controlada
6. Crescimento do número de usuários
7. Escalabilidade da infraestrutura
8. Distribuição das requisições entre servidores

---

# 🚀 Tecnologias

- Python
- Flask
- Docker
- Docker Compose
- Redis
- HTML5
- CSS3
- JavaScript

Infraestrutura prevista:

- AWS EC2
- Application Load Balancer
- Auto Scaling Group
- Amazon ECR
- Terraform (em desenvolvimento)

---

# 📂 Estrutura

```text
cloud-black-friday-demo/

├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── data/
│   └── store.json
│
├── static/
│   ├── app.js
│   ├── styles.css
│   └── images/
│
├── templates/
│   └── index.html
│
└── README.md
```

---

# ⚙️ Personalização

Todas as informações da loja podem ser alteradas através de:

```text
data/store.json
```

É possível modificar:

- nome da loja
- banner principal
- produtos
- imagens
- preços
- descontos
- descrições
- avaliações
- cronômetro
- textos da Black Friday

---

# ▶️ Executando localmente

Clone o projeto:

```bash
git clone https://github.com/aryaneandrade/cloud-black-friday-demo.git

cd cloud-black-friday-demo
```

Inicie a aplicação:

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:8080
```

---

# ☁️ Arquitetura (Roadmap)

A próxima etapa do projeto consiste em publicar a aplicação na AWS utilizando a arquitetura abaixo.

```text
GitHub
   │
   ▼
Amazon ECR
   │
   ▼
Application Load Balancer
   │
   ▼
Auto Scaling Group
   │
 ┌───────────────┐
 │               │
EC2          EC2
 │               │
 └──────┬────────┘
        │
      Redis
```

---

# 📚 Objetivos de aprendizagem

Este projeto demonstra conceitos como:

- Computação em Nuvem
- Escalabilidade Horizontal
- Balanceamento de Carga
- Auto Scaling
- Alta Disponibilidade
- Containers
- Virtualização
- Infraestrutura como Código

---

# 📌 Status

✅ Desenvolvimento local concluído

🚧 Publicação na AWS em andamento

🚧 Terraform em desenvolvimento

---

# 👩‍💻 Autora

Aryane Andrade

Estudante de Ciência da Computação

Estagiária em Monitoramento de Infraestrutura, Sistemas e Cloud

---

# 📄 Licença

Projeto desenvolvido exclusivamente para fins educacionais.