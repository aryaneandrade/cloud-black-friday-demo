#!/bin/bash

set -euxo pipefail

exec > >(tee /var/log/cloud-bf-bootstrap.log | logger -t cloud-bf-user-data -s 2>/dev/console) 2>&1

AWS_REGION="us-east-1"
ECR_REGISTRY="424051028739.dkr.ecr.us-east-1.amazonaws.com"
APP_IMAGE="${ECR_REGISTRY}/cloud-black-friday-demo:v1.2.3"
REDIS_URL="redis://172.31.22.6:6379/0"

echo "=== Iniciando configuração da Cloud Black Friday Demo ==="

# Instala e inicia o Docker.
dnf install -y docker
systemctl enable --now docker

# Aguarda o Docker ficar disponível.
for attempt in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
        echo "Docker disponível."
        break
    fi

    echo "Aguardando Docker: tentativa ${attempt}/30"
    sleep 5
done

docker info >/dev/null

# Autentica no Amazon ECR usando a IAM Role da EC2.
for attempt in $(seq 1 12); do
    if aws ecr get-login-password --region "${AWS_REGION}" \
        | docker login \
            --username AWS \
            --password-stdin "${ECR_REGISTRY}"; then
        echo "Login no ECR realizado."
        break
    fi

    echo "Falha temporária no login do ECR: tentativa ${attempt}/12"
    sleep 10
done

# Baixa a versão fixa da aplicação.
docker pull "${APP_IMAGE}"

# Remove uma versão antiga, caso exista.
docker rm -f cloud-bf-app 2>/dev/null || true

# Inicia a aplicação apontando para o Redis compartilhado.
docker run -d \
    --name cloud-bf-app \
    --restart unless-stopped \
    -p 8080:8080 \
    -e APP_NAME="NovaStore" \
    -e COUNTDOWN_SECONDS="10" \
    -e STORE_CONFIG_PATH="/app/data/store.json" \
    -e REDIS_URL="${REDIS_URL}" \
    "${APP_IMAGE}"

# Aguarda o endpoint de saúde responder.
for attempt in $(seq 1 30); do
    if curl --fail --silent http://localhost:8080/health >/dev/null; then
        echo "Aplicação saudável."
        echo "=== Configuração concluída com sucesso ==="
        exit 0
    fi

    echo "Aguardando aplicação: tentativa ${attempt}/30"
    sleep 5
done

echo "ERRO: a aplicação não ficou saudável dentro do prazo."
docker logs cloud-bf-app || true
exit 1