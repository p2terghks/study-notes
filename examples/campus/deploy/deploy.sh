#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${AWS_REGION:?Set AWS_REGION, e.g. ap-northeast-2}"
: "${STACK_NAME:?Set STACK_NAME, e.g. campus-prod}"
: "${CERTIFICATE_ARN:?Set the ISSUED ACM certificate ARN in the same region}"
# infra는 기반 리소스 생성, app은 이미지 업로드와 서비스 생성/갱신이다.
phase="${1:-}"
[[ "$phase" == infra || "$phase" == app ]] || { echo 'Usage: deploy/deploy.sh infra|app' >&2; exit 1; }
command -v aws >/dev/null
params=(
  "CertificateArn=$CERTIFICATE_ARN"
  "DesiredCount=${DESIRED_COUNT:-2}"
  "DatabaseMultiAZ=${DATABASE_MULTI_AZ:-true}"
  "DatabaseClass=${DATABASE_CLASS:-db.t4g.micro}"
)
if [[ "$phase" == app ]]; then
  : "${IMAGE_TAG:?Set a NEW immutable image tag, e.g. release-20260918-1}"
  command -v docker >/dev/null
  repository="$(aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue | [0]' --output text)"
  [[ "$repository" != None && -n "$repository" ]] || { echo 'Create the infrastructure first.' >&2; exit 1; }
  registry="${repository%%/*}"
  aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$registry"
  # Apple Silicon에서도 Fargate 태스크 정의와 일치하는 X86_64 이미지를 업로드한다.
  docker buildx build --platform linux/amd64 --provenance=false --tag "$repository:$IMAGE_TAG" --push .
  params+=("ImageUri=$repository:$IMAGE_TAG")
else
  # ImageUri가 빈 infra 단계로 기존 스택을 덮어쓰면 서비스가 삭제될 수 있으므로 차단한다.
  if aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" >/dev/null 2>&1; then
    echo 'Stack already exists. Use app to update, or update the template explicitly preserving ImageUri.' >&2
    exit 1
  fi
fi
aws cloudformation deploy --region "$AWS_REGION" --stack-name "$STACK_NAME" \
  --template-file deploy/ecs-fargate.json --capabilities CAPABILITY_IAM \
  --parameter-overrides "${params[@]}" --no-fail-on-empty-changeset
aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs' --output table
