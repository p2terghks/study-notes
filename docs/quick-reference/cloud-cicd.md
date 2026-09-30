# 프로젝트 3 · Docker와 ECS CI/CD

## 목표와 선택한 방식

**테스트 → 이미지 빌드 → ECR push → 마이그레이션 → ECS 롤링 배포 → 결과 확인**을 자동화합니다. 이 예제는 GitHub Actions와 ECS Fargate를 사용합니다. EKS 클러스터 운영과 Jenkins 서버 구축은 별도 확장 과제로 구분합니다.

[전체 코드 ZIP](sample-files/cloud-projects.zip)의 `app/`, `infra/ecs/`, `scripts/deploy-ecs.py`, `workflows/deploy-ecs.yml.example`을 확인하세요. 현재는 로컬 테스트와 코드 검증만 수행하며 워크플로는 활성화하지 않습니다.

## 컨테이너 이미지와 실행 환경

| 파일/설정 | 역할 |
|---|---|
| app/Dockerfile | Node 22 런타임, npm ci, 일반 사용자 실행 |
| app/package-lock.json | 실제 의존성 버전 고정 |
| APP_VERSION | 요청을 처리한 릴리스 표시 |
| DB_SECRET_ARN | AWS에서 관리 암호 조회 |
| DB_SSL=true | RDS CA로 서버 인증서 검증 |
| SIGTERM 처리 | 기존 요청 정리 후 프로세스 종료 |

`latest` 태그 대신 ECR digest URI로 실행합니다. DB 암호를 이미지나 환경 예제에 복사하지 않습니다. 로컬 Compose 암호는 격리된 학습 DB에만 사용합니다. 베이스 이미지 태그도 시간이 지나면 바뀌므로 실제 운영에서는 검증한 digest 고정을 추가하세요.

## 로컬 개발 루프

```bash
node --test app/test/*.test.cjs
docker compose up -d --build --scale app=2
curl -fsS http://localhost:8088/api/info
python3 scripts/test_deploy.py
```

앱 내용을 변경한 뒤 이미지를 다시 만들고 저장·조회가 동작하는지 확인합니다. Compose의 재생성은 ECS 롤링 배포와 동일한 무중단 보장을 제공하지 않습니다. DB 테이블 변경은 `--migrate` 명령으로 분리되어 있으며 현재 마이그레이션은 테이블 생성만 합니다.

## 파이프라인의 각 단계

```text
main push
  → npm ci / API 테스트 / 의존성 검사
  → GitHub OIDC 임시 자격증명
  → linux/amd64 이미지 빌드
  → 실행별 고유 태그로 ECR push
  → digest로 새 task definition 등록
  → 같은 네트워크에서 마이그레이션 task 실행·종료 코드 확인
  → ECS service 갱신
  → 안정 상태 대기 + 정확한 새 revision인지 확인
```

워크플로에 `concurrency`를 설정해 같은 환경 배포가 겹치지 않게 합니다. 재실행에서도 ECR 불변 태그와 충돌하지 않도록 commit SHA·run ID·attempt를 태그에 포함합니다.

## 최초 ECS 준비와 OIDC 설정

AWS 적용 단계는 이번 범위 밖입니다. 나중에 적용할 때는 IaC 가이드로 ECR 이미지를 먼저 준비한 뒤 ECS 스택을 만듭니다.

1. 첫 Terraform 적용은 `desired_count=0`으로 수행해 마이그레이션 전 앱이 반복 실패하지 않게 합니다.
2. GitHub OIDC provider가 계정에 이미 있으면 해당 ARN을 사용합니다. 계정별 하나를 관리하고 중복 생성하지 않습니다.
3. `github_oidc_provider_arn`, `github_oidc_subject`, `ecr_repository_arn`을 입력하면 제한된 CI 역할이 생성됩니다.
4. GitHub의 `dev` Environment를 만들고 배포 브랜치 규칙을 설정합니다.
5. Environment 변수 `AWS_REGION`, `AWS_ROLE_ARN`, `ECR_REPOSITORY`(이름), `ECS_CLUSTER`, `ECS_SERVICE`를 채웁니다.
6. 템플릿을 저장소 루트의 `.github/workflows/deploy-ecs.yml`로 복사합니다. 현재의 `cloud-projects/` 경로 구조를 유지합니다.
7. 첫 수동 실행으로 마이그레이션과 서비스 2개 실행을 확인한 뒤 main push 배포를 사용합니다.

OIDC의 `sub`는 실제 저장소의 형식을 정확히 넣습니다. Environment를 쓰므로 `...:environment:dev` 형태를 확인하고, 변경 불가능한 소유자/저장소 ID가 포함되는 계정 설정이라면 그 형식을 맞춰야 합니다. 전체 저장소/모든 브랜치 와일드카드로 풀지 않습니다. [GitHub 공식 AWS OIDC](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)

## 롤링 배포가 요청을 유지하는 조건

```hcl
deployment_minimum_healthy_percent = 100
deployment_maximum_percent         = 200
deployment_circuit_breaker {
  enable   = true
  rollback = true
}
```

정상 task 2개를 유지하면서 새 task를 추가할 공간을 허용합니다. CPU·메모리·IP·계정 할당량·DB 연결 여유가 필요합니다. `/readyz`가 성공한 새 대상에 트래픽이 가고 기존 대상은 draining 후 종료됩니다. [AWS ECS 롤링 배포](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html)

circuit breaker는 실패 배포를 감지하고 이전에 완료된 배포로 돌아갈 수 있습니다. 첫 배포에는 성공 이력이 없을 수 있습니다. 안정 상태가 되었다고 새 버전 성공으로 단정하지 않도록 배포 스크립트는 PRIMARY task definition이 요청한 revision인지도 확인합니다. [공식 circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentCircuitBreaker.html)

## 무중단 배포 실험과 롤백

1. 배포 전 `scripts/probe.py`로 요청을 지속 기록합니다.
2. APP_VERSION이 새 digest로 바뀌는지 확인합니다.
3. 새 컨테이너만 준비 검사에 실패하도록 만든 테스트 버전을 제한된 환경에서 배포합니다.
4. 이전 revision 복구, 오류 수, 복구 시간을 기록합니다.
5. 마이그레이션 실패 시 서비스 revision이 바뀌지 않는지도 확인합니다.

자동 롤백과 별개로 이전 task definition ARN을 기록해 수동 복귀할 수 있게 합니다. 아래는 실제 대상 값을 확인한 뒤 실행하는 예시입니다.

```bash
aws ecs update-service --cluster CLUSTER --service SERVICE --task-definition PREVIOUS_TASK_ARN
aws ecs wait services-stable --cluster CLUSTER --services SERVICE
```

DB 변경은 이미지 롤백으로 되돌아가지 않습니다. 새 컬럼 추가 → 구/신 버전 동시 호환 → 구 버전 제거 → 나중에 컬럼 삭제처럼 호환 가능한 마이그레이션을 설계합니다. 이번 기본 예제는 파괴적 마이그레이션을 수행하지 않습니다.

## Terraform과 배포 도구의 관리 경계

Terraform은 네트워크·IAM·서비스 설정을 관리하고 CI가 앱 revision과 실행 수를 갱신합니다. `ignore_changes`로 반복 apply가 이전 이미지로 되돌리지 않게 했습니다. 초기 task definition을 Terraform에서 바꿨다고 실행 중 서비스에 자동 배포되지는 않습니다.

task CPU·환경·역할 같은 정의를 변경할 때는 새 task definition과 실제 서비스 참조를 함께 검토하고 명시적으로 릴리스해야 합니다. `deploy-ecs.py`는 현재 서비스 정의를 복사해 이미지와 APP_VERSION을 바꾸므로 다른 변경을 자동으로 끌어오지 않습니다.

Blue/Green은 별도 대상 그룹·전환·추가 용량·롤백 정책을 갖추는 확장 방식입니다. 이 코드에 구현된 방식은 **Rolling**입니다. [공식 워크플로 액션](https://github.com/aws-actions/configure-aws-credentials)에서 버전 변경을 확인하고 운영 적용 때 액션도 검증한 SHA로 고정하세요.
