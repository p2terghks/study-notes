# Kubernetes · Terraform 로컬 학습 예제

[상세 강의 노트](../../kubernetes-terraform-guide.html) 또는 온라인 [강의 노트](https://p2terghks.github.io/study-notes/docs/quick-reference/kubernetes-terraform-guide.html)의 16~30절과 함께 사용하세요.

## 폴더

- `kubernetes/demo.yaml`: Namespace, ConfigMap, Deployment, Service를 만드는 YAML 실습.
- `terraform-basics/main.tf`: 클라우드 없이 terraform_data로 입력·계획·상태를 배우는 실습. Terraform 1.4 이상.
- `terraform-kubernetes/main.tf`: 기존 로컬 kind 클러스터에 별도 namespace와 앱을 만드는 실습. Kubernetes provider 2.38.x 사용.
- `terraform-kubernetes/.terraform.lock.hcl`: 선택한 provider 버전과 체크섬.

## 전제와 순서

1. Docker 등의 컨테이너 실행 환경, kind, kubectl, Terraform을 준비합니다.
2. 강의 16절대로 `lecture-local` 클러스터를 만들고 `~/.kube/lecture-kind.yaml` 전용 설정을 사용합니다. 같은 이름·파일이 있으면 먼저 기존 용도를 확인합니다.
3. 이 폴더에서 `kubectl apply -f kubernetes/demo.yaml`로 YAML 실습을 진행합니다. namespace는 `lecture-demo`입니다.
4. `terraform-basics`에서 init → validate → plan → 검토 → apply를 실습합니다. 실제 서버는 만들어지지 않습니다.
5. `terraform-kubernetes`에서 같은 흐름을 진행합니다. namespace는 `lecture-tf`입니다. provider 설치에는 인터넷이 필요합니다.
6. 강의 30절대로 Terraform 관리 객체, YAML 객체, 클러스터 순으로 삭제합니다.

명령은 macOS/Linux bash·zsh 기준입니다. 예제 이미지 태그는 학습용이며 최신 보안 버전 추천이 아닙니다. 실제 비밀번호·토큰·state·저장된 plan을 Git에 올리지 마세요.

## 검증 범위

Terraform 1.16.5에서 두 구성의 형식·validate를 확인했고 기초 실습은 생성, 무변경 재계획, 입력 변경, 잘못된 입력 거부, 삭제까지 실행했습니다. YAML 구조·선택자·포트·ConfigMap 연결을 정적으로 확인했습니다. 로컬 Docker 연결 문제로 Kubernetes 실제 배포·접속 및 Kubernetes provider plan/apply는 실행 검증하지 못했습니다. AWS 자원은 생성하지 않습니다.
