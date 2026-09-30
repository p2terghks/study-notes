# 프로젝트 2 · Terraform 인프라 자동화

## 목표와 코드 구성

**프로젝트 1의 구조를 코드로 선언하고 환경별 상태를 분리**합니다. Terraform은 파일을 실행 순서대로 처리하는 셸이 아니라 리소스 의존 관계를 계산해 목표 상태로 맞추는 도구입니다.

[전체 코드 ZIP](sample-files/cloud-projects.zip)의 `cloud-projects/infra`를 확인하세요.

```text
infra/
├── bootstrap/        상태 버킷·ECR·선택적 기존 잠금 테이블
├── modules/
│   ├── network/      두 AZ의 VPC·서브넷·NAT
│   ├── database/     RDS·DB SG·백업
│   └── vm-tier/      EC2 템플릿·ASG·확장 정책
├── three-tier/       프로젝트 1 EC2 구성
├── ecs/              프로젝트 3 Fargate 구성
└── serverless/       프로젝트 4 이벤트 구성
```

각 스택에 Dev·Stg·Prd 변수 예시와 backend 예시가 있습니다. 프로젝트 1과 2는 같은 인프라를 설명과 코드 관점에서 다루므로 두 번 배포할 필요가 없습니다.

## 핵심 명령과 책임 범위

| 명령 | 역할 |
|---|---|
| terraform fmt | 코드 서식 통일 |
| terraform init | 모듈·프로바이더·backend 초기화 |
| terraform validate | 문법·참조·프로바이더 스키마 검사 |
| terraform plan | 현재 상태와 목표 상태 차이 계산 |
| terraform apply | 계획에 따라 리소스 변경 |
| terraform destroy | 상태에 기록된 관리 리소스 삭제 |

현재 개발 범위에서는 `init -backend=false`, `validate`, AWS를 호출하지 않는 mock provider 기반 `terraform test`를 실행합니다. 실제 AWS plan/apply는 수행하지 않습니다. 정적 검증이 IAM 권한, 서비스 할당량, 실제 배포 성공을 보장하지는 않습니다.

## 상태 파일 — S3 잠금과 기존 DynamoDB 방식

상태 파일은 리소스와 Terraform 주소의 대응표입니다. 자격증명과 민감한 값이 들어갈 수 있으므로 Git에 올리지 않습니다. S3 버전 관리·암호화·공개 차단·TLS 강제를 사용합니다.

```hcl
bucket       = "계정-리전-고유한-상태버킷"
key          = "three-tier/dev/terraform.tfstate"
region       = "ap-northeast-2"
encrypt      = true
use_lockfile = true
```

새 코드는 **S3 자체 잠금**을 사용합니다. DynamoDB 잠금은 현재 deprecated이며, `bootstrap`의 `create_legacy_lock_table=true`는 기존 구성 이해·마이그레이션용 선택지입니다. 이 경우 기존 backend의 `dynamodb_table`에는 `portfolio-legacy-state-lock`을 지정하고, 팀의 Terraform 버전을 맞춰 S3 잠금으로 전환합니다. 활성 작업 중 잠금을 강제로 제거하지 않습니다. [HashiCorp 공식 S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)

## 계정 없이 로컬에서 검증하기

Terraform 1.13 이상을 설치합니다. 서버리스 ZIP은 서버리스 가이드의 패키징 절차로 먼저 만듭니다. 다음 명령은 `cloud-projects`에서 실행합니다.

```bash
terraform fmt -check -recursive infra
terraform -chdir=infra/three-tier init -backend=false
terraform -chdir=infra/three-tier validate
```

`bootstrap`, `ecs`, `serverless`에도 같은 방식으로 검사합니다. provider 잠금 파일은 커밋하고 `.terraform/`, 상태·계획·실제 tfvars·backend 파일은 제외합니다. 계획 파일도 민감할 수 있어 공개 저장소에 첨부하지 않습니다.

## AWS 적용 준비 순서 — 추후 배포할 때

아래는 계정·리전·예산을 정한 뒤 사용하는 절차이며 이번 작업에서는 실행하지 않습니다.

1. AWS CLI/SSO로 로그인하고 `aws sts get-caller-identity`로 대상 계정을 확인합니다.
2. `infra/bootstrap/terraform.tfvars.example`을 실제 값으로 복사합니다. 버킷 이름은 전역 고유해야 합니다.
3. bootstrap은 로컬 상태로 plan/apply하여 S3와 ECR을 만듭니다. 이 상태도 안전하게 보관하고 별도 관리 backend로 이전할 수 있습니다. bootstrap 자원을 하위 프로젝트와 함께 삭제하지 않습니다.
4. `app/`에서 linux/amd64 이미지를 빌드하고 ECR에 push한 뒤 digest URI를 얻습니다.
5. 스택의 `dev.tfvars.example`을 `dev.auto.tfvars`로, `dev.backend.hcl.example`을 `backend.hcl`로 복사하여 계정 값·허용 IP·이미지를 채웁니다.
6. 실제 backend로 다시 `init`하고 저장한 계획을 검토합니다.

```bash
terraform -chdir=infra/three-tier init -reconfigure -backend-config=backend.hcl
terraform -chdir=infra/three-tier plan -out=review.tfplan
terraform -chdir=infra/three-tier apply review.tfplan
```

`-backend=false` 초기화 후 로컬 리소스 상태가 이미 존재하는 경우에는 무조건 `-reconfigure`로 바꾸지 말고 `init -migrate-state`로 이전해야 하는지 확인하세요. 자격증명을 tfvars에 적지 않습니다.

## 이미지 부트스트랩 — 최초 한 번

리소스가 준비된 뒤에만 사용하는 명령 예시입니다. `ACCOUNT`, `REGION`, `REPOSITORY`를 실제 값으로 설정합니다.

```bash
export AWS_REGION=ap-northeast-2
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REPOSITORY=cloud-portfolio-app
REGISTRY="$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"
aws ecr get-login-password | docker login --username AWS --password-stdin "$REGISTRY"
docker build --platform linux/amd64 -t "$REGISTRY/$REPOSITORY:bootstrap-1" app
docker push "$REGISTRY/$REPOSITORY:bootstrap-1"
aws ecr describe-images --repository-name "$REPOSITORY" --image-ids imageTag=bootstrap-1 --query 'imageDetails[0].imageDigest' --output text
```

`image_uri`에는 `레지스트리/저장소@sha256:다이제스트`를 넣습니다. ECR 태그는 불변이라 같은 태그를 덮어쓰지 말고 새 릴리스마다 새 태그를 사용합니다. Apple Silicon에서도 EC2·ECS 예제는 x86_64이므로 플랫폼을 맞춰 빌드합니다.

## Dev · Stg · Prd 분리

| 구분 | Dev | Stg | Prd |
|---|---|---|---|
| 목적 | 변경 실험 | 운영 전 검증 | 실제 운영 |
| 상태 키 | 스택/dev/... | 스택/stg/... | 스택/prd/... |
| 변수 | dev 예시 기반 | stg 예시 기반 | prd 예시 기반 |
| 권한 | 개발 범위 | 검증 범위 | 배포 권한 제한 |

실행 디렉터리나 체크아웃을 환경별로 나누고 한 폴더에 여러 `*.auto.tfvars`를 두지 않습니다. 예시는 이름·상태 분리를 제공하며, 더 강한 격리는 AWS 계정 자체를 분리해 구현합니다. 같은 VPC CIDR을 쓰는 환경끼리 연결할 예정이라면 주소도 겹치지 않게 계획합니다.

NAT·Multi-AZ·삭제 보호는 기본 켜짐입니다. 비용 때문에 끌 경우 어떤 장애에 취약해지는지 기록합니다. 운영급 구성에서는 인증·DB 최소 권한·감사 로그·실제 백업 복원 검증을 추가해야 합니다.

## 삭제와 복구를 코드만큼 자세히 기록하기

1. 서비스의 데이터·상태·백업을 확인합니다.
2. RDS 삭제 보호를 해제하는 변경을 별도 검토·적용합니다.
3. `plan -destroy`로 삭제 대상을 확인하고 destroy를 실행합니다.
4. RDS 최종 스냅샷 이름이 이미 존재하면 충돌하지 않는 이름으로 바꿉니다.
5. S3는 비어 있지 않으면 삭제되지 않습니다. 버전 객체·delete marker도 확인합니다.
6. 최종 스냅샷·ECR 이미지·S3 상태·로그·Elastic IP가 남았는지 확인합니다.

코드는 RDS 최종 스냅샷을 남기고 ECR/S3 강제 삭제를 기본으로 사용하지 않습니다. 잔존 데이터에는 비용이 발생할 수 있습니다. ‘destroy 성공=계정 비용 0’으로 기록하지 않습니다.

포트폴리오에는 모듈 의존 관계, 환경별 계획 차이, 상태 잠금 충돌 실험, 재생성 과정, 남는 리소스 목록을 첨부합니다.
