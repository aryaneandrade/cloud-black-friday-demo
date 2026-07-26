#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="${ROOT_DIR}/terraform"
PLAN_FILE="${TF_DIR}/.destroy.tfplan"

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

command -v aws >/dev/null 2>&1 \
  || error "AWS CLI não está instalada."

command -v terraform >/dev/null 2>&1 \
  || error "Terraform não está instalado."

aws sts get-caller-identity --no-cli-pager >/dev/null \
  || error "Não foi possível autenticar na AWS."

cd "${TF_DIR}"

log "Inicializando o Terraform"
terraform init -input=false

log "Recursos atualmente controlados"

terraform state list || true

printf '\nATENÇÃO: esta operação removerá:\n'
printf -- '- Application Load Balancer\n'
printf -- '- Auto Scaling Group e instâncias EC2\n'
printf -- '- EC2 do Redis\n'
printf -- '- Security Groups\n'
printf -- '- IAM Role e Instance Profile\n'
printf -- '- ECR e todas as imagens\n\n'
printf 'A VPC padrão e as sub-redes não serão removidas.\n\n'

read -r -p "Digite DESTRUIR para continuar: " CONFIRMATION

if [[ "${CONFIRMATION}" != "DESTRUIR" ]]; then
  printf 'Operação cancelada.\n'
  exit 0
fi

log "Gerando o plano de destruição"

terraform plan \
  -destroy \
  -input=false \
  -out="${PLAN_FILE}"

log "Aplicando o plano de destruição"

terraform apply \
  -input=false \
  -auto-approve \
  "${PLAN_FILE}"

printf '\n\033[1;32mInfraestrutura removida com sucesso.\033[0m\n'
printf 'A VPC padrão e o código do projeto foram preservados.\n'
