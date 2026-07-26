#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="${ROOT_DIR}/terraform"
PLAN_FILE="${TF_DIR}/.deploy.tfplan"

export AWS_PAGER=""

cleanup() {
  rm -f "${PLAN_FILE}"
}

trap cleanup EXIT

log() {
  printf '\n\033[1;34m==> %s\033[0m\n' "$1"
}

error() {
  printf '\n\033[1;31mERRO: %s\033[0m\n' "$1" >&2
  exit 1
}

check_command() {
  command -v "$1" >/dev/null 2>&1 \
    || error "O comando '$1' não está instalado."
}

log "Validando dependências"

for command_name in aws docker terraform curl; do
  check_command "${command_name}"
done

docker info >/dev/null 2>&1 \
  || error "O Docker não está ativo ou seu usuário não possui acesso ao daemon."

aws sts get-caller-identity --no-cli-pager >/dev/null \
  || error "Não foi possível autenticar na AWS."

AWS_REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || true)}"
AWS_REGION="${AWS_REGION:-us-east-1}"

log "Região AWS: ${AWS_REGION}"

cd "${TF_DIR}"

log "Inicializando o Terraform"
terraform init -input=false

log "Verificando formatação"
terraform fmt -check -recursive

log "Validando a configuração"
terraform validate

log "Criando ou validando o repositório ECR"

terraform apply \
  -input=false \
  -auto-approve \
  -target=aws_ecr_repository.app

ECR_REPOSITORY_URL="$(terraform output -raw ecr_repository_url)"
ECR_IMAGE="$(terraform output -raw ecr_image)"
ECR_REGISTRY="${ECR_REPOSITORY_URL%%/*}"

log "Repositório: ${ECR_REPOSITORY_URL}"
log "Imagem: ${ECR_IMAGE}"

log "Autenticando o Docker no Amazon ECR"

aws ecr get-login-password \
  --region "${AWS_REGION}" \
  | docker login \
      --username AWS \
      --password-stdin "${ECR_REGISTRY}"

log "Construindo a imagem Docker"

docker build \
  --pull \
  --tag "${ECR_IMAGE}" \
  "${ROOT_DIR}"

log "Publicando a imagem no Amazon ECR"

docker push "${ECR_IMAGE}"

log "Gerando o plano completo da infraestrutura"

terraform plan \
  -input=false \
  -out="${PLAN_FILE}"

log "Aplicando o plano"

terraform apply \
  -input=false \
  -auto-approve \
  "${PLAN_FILE}"

APPLICATION_URL="$(terraform output -raw application_url)"

log "Aguardando a aplicação ficar disponível"

APPLICATION_READY=false

for attempt in $(seq 1 36); do
  if curl \
    --fail \
    --silent \
    --show-error \
    "${APPLICATION_URL}/health" >/dev/null 2>&1; then

    APPLICATION_READY=true
    break
  fi

  printf 'Tentativa %s/36: aguardando aplicação...\n' "${attempt}"
  sleep 10
done

if [[ "${APPLICATION_READY}" != "true" ]]; then
  printf '\nA infraestrutura foi criada, mas o health check ainda não respondeu.\n'
  printf 'Verifique o Target Group e os logs de inicialização das instâncias.\n'
  printf 'URL: %s\n' "${APPLICATION_URL}"
  exit 1
fi

printf '\n\033[1;32mDeploy concluído com sucesso!\033[0m\n'
printf 'Aplicação: %s\n' "${APPLICATION_URL}"
printf 'Imagem:    %s\n' "${ECR_IMAGE}"
printf 'ASG:       %s\n' "$(terraform output -raw autoscaling_group_name)"
printf 'Redis IP:  %s\n' "$(terraform output -raw redis_private_ip)"
