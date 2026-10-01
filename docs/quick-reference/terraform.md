# Terraform 사용법

## Terraform과 IaC의 의미

**Terraform은 원하는 인프라 상태를 코드로 선언하고, 현재 상태와 비교하여 변경을 적용하는 도구입니다.** IaC(Infrastructure as Code)는 이런 인프라 구성을 코드로 관리하는 방식입니다.

```text
설정 코드(.tf) + state + provider가 조회한 실제 자원
    → plan: 무엇을 만들고·바꾸고·삭제할지 계산
    → apply: 계획을 적용하고 state 갱신
```

AWS CLI가 “인스턴스를 시작해” 같은 API 작업을 직접 호출한다면 Terraform은 “이 설정의 인스턴스가 존재해야 해”를 선언합니다. Terraform이 모든 수동 변경을 자동 복구하는 상시 실행 데몬인 것은 아닙니다. plan/apply 등 실행 시 상태를 비교합니다.

[Terraform CLI 개요](https://developer.hashicorp.com/terraform/cli/commands)

## 설치·버전과 작업 디렉터리

[공식 설치 안내](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)에서 OS·CPU에 맞는 CLI를 설치한 뒤 확인합니다.

```bash
terraform version
terraform -help
terraform plan -help
```

같은 디렉터리의 `.tf` 파일들은 **한 모듈의 설정으로 함께 읽힙니다.** 파일 이름순으로 실행되는 스크립트가 아닙니다. 다른 실습의 `main.tf`를 같은 폴더에 모아 두지 마세요.

```text
my-infra/
  versions.tf       Terraform·provider 버전 조건
  providers.tf      API 연결 대상·리전 설정
  main.tf           리소스·모듈 구성
  variables.tf      입력 선언
  outputs.tf        결과 출력
  dev.tfvars        환경별 입력 값
```

파일 이름은 관례이며 역할을 나눠 읽기 쉽게 만든 것입니다. 다른 폴더에서 실행할 때는 `terraform -chdir=my-infra plan`처럼 **하위 명령 앞에** `-chdir`를 둡니다.

## 핵심 명령어: init → plan → apply

| 명령 | 역할 | 알아둘 점 |
| --- | --- | --- |
| `terraform init` | backend·provider·module 초기화 | 다운로드·backend 접근이 필요할 수 있음 |
| `terraform fmt -recursive` | 코드 형식 정리 | 파일을 수정함 |
| `terraform fmt -check -recursive` | 형식 준수 확인 | 형식이 다르면 실패 코드 |
| `terraform validate` | 설정 문법·타입·내부 일관성 검사 | 실제 클라우드 권한·할당량까지 보장하지 않음 |
| `terraform plan` | 변경 계획 계산 | 기본적으로 실제 자원 조회도 수행 |
| `terraform apply` | 새 계획을 보여주고 확인 후 적용 | 실제 자원 변경 가능 |
| `terraform output` | state에 저장된 출력 확인 | 반드시 실시간 클라우드 조회는 아님 |
| `terraform destroy` | 관리 자원 삭제 계획·적용 | 현재 작업 공간과 state의 대상 확인 |

설정·provider·backend·module을 추가하거나 바꾸면 필요한 초기화를 위해 `init`을 다시 실행합니다. `init -upgrade`는 허용된 버전 범위 안에서 의존성을 갱신하므로 일반 init과 구분합니다.

## HCL 블록·참조 읽는 법

```hcl
variable "environment" {
  type    = string
  default = "dev"
}

locals {
  label = "study-${var.environment}"
}

resource "terraform_data" "note" {
  input = local.label
}

output "label" {
  value = terraform_data.note.output
}
```

| 구문 | 읽는 방법 |
| --- | --- |
| `variable "environment"` | 외부에서 받을 입력 선언 |
| `var.environment` | 입력 값 참조 |
| `locals { ... }` | 계산한 값에 이름 붙이기 |
| `local.label` | 로컬 값 참조 |
| `resource "종류" "이름"` | Terraform이 관리할 자원 선언 |
| `terraform_data.note.output` | 해당 자원의 속성 참조 |
| `output "label"` | 호출자·사용자에게 노출할 결과 |

이 예제의 `terraform_data`는 내장 리소스로 외부 서버를 만들지 않습니다. 로컬 state에 값을 저장하여 리소스의 생성·갱신 흐름을 연습할 수 있습니다.

[terraform_data 공식 설명](https://developer.hashicorp.com/terraform/language/resources/terraform-data)

## 변수·타입·tfvars·우선순위

```hcl
variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "stg", "prd"], var.environment)
    error_message = "environment는 dev, stg, prd 중 하나여야 합니다."
  }
}

variable "labels" {
  type    = map(string)
  default = { owner = "study" }
}
```

`string`, `number`, `bool`, `list(string)`, `set(string)`, `map(string)`, `object({...})` 등으로 입력 구조를 정합니다. `dev.tfvars`에는 선언 블록 없이 값만 적습니다.

```hcl
# dev.tfvars
 environment = "dev"
 labels = { owner = "study", project = "practice" }
```

```bash
terraform plan -var-file=dev.tfvars
terraform plan -var='environment=stg'
```

로컬 CLI의 일반적인 우선순위는 낮은 쪽부터 `default` → `TF_VAR_이름` 환경 변수 → `terraform.tfvars` → `terraform.tfvars.json` → 이름순의 `*.auto.tfvars`/JSON → 명령행 `-var`·`-var-file` 지정 순서입니다. `dev.tfvars`는 자동 로드 이름이 아니므로 `-var-file`로 지정합니다. HCP Terraform의 workspace 변수 등은 별도 적용 규칙을 확인합니다.

[입력 변수](https://developer.hashicorp.com/terraform/language/values/variables)

## Provider·resource·data의 차이

| 구분 | 역할 |
| --- | --- |
| Terraform CLI | 그래프·계획·state·실행 흐름 관리 |
| provider | AWS 등 외부 서비스 API를 다루는 플러그인 |
| resource | Terraform이 생성·수정·삭제를 관리할 대상 |
| data | 기존 정보 조회; 해당 자원의 수명주기를 직접 관리하지 않음 |

AWS 연결 설정의 예시입니다. 실제 사용할 provider 버전 조건은 프로젝트에 맞게 검토합니다.

```hcl
terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.14.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-2"
}

data "aws_caller_identity" "current" {}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}
```

`~> 6.14.0`은 6.14.x 범위이며 6.15는 포함하지 않습니다. `~> 6.14`는 6.x의 이후 minor도 허용하므로 다릅니다. 인증 키를 HCL에 직접 쓰기보다 지원되는 프로파일·환경의 역할을 사용합니다.

```bash
# bash/zsh: 이 명령에만 프로파일 적용
AWS_PROFILE=study terraform plan
```

SSO 세션이 만료되면 AWS CLI로 다시 로그인합니다. AWS CLI의 새 로그인 방식은 provider·SDK 버전에 따라 지원 여부가 다를 수 있습니다.

[Provider 설정](https://developer.hashicorp.com/terraform/language/providers/configuration)

## plan 기호·저장 계획·종료 코드

| 표시 | 뜻 |
| --- | --- |
| `+` | 생성 |
| `~` | 같은 자원 갱신 |
| `-` | 삭제 |
| `-/+` 또는 `+/-` | 삭제와 생성이 필요한 교체 |
| `(known after apply)` | 적용 후 확정될 값 |

```bash
terraform plan -out=review.tfplan
terraform show review.tfplan
terraform apply review.tfplan
```

**저장된 계획을 `apply review.tfplan`으로 적용하면 추가 yes 확인 없이 실행됩니다.** 먼저 show 결과를 검토해야 합니다. 계획 파일에는 입력·민감한 데이터가 포함될 수 있어 Git에 올리지 않습니다. state가 변경되어 오래된 계획이 되었다면 새로 plan합니다.

자동화에서 `terraform plan -detailed-exitcode`는 0=변경 없음, 1=오류, 2=변경 있음입니다. 2를 무조건 장애로 처리하지 않도록 스크립트를 작성합니다. `plan`은 비용 견적이나 모든 실행 성공을 보장하는 단계가 아닙니다.

[plan 옵션·모드](https://developer.hashicorp.com/terraform/cli/commands/plan)

## count·for_each·의존성

같은 유형의 자원을 여러 개 선언할 때 `count` 또는 `for_each`를 사용합니다. 하나의 블록에 둘을 동시에 쓰지 않습니다.

```hcl
resource "terraform_data" "service" {
  for_each = toset(["web", "api"])
  input    = "${each.key}-dev"
}
```

주소는 `terraform_data.service["web"]`, `terraform_data.service["api"]`입니다. `count`는 `[0]`, `[1]` 같은 인덱스를 사용하므로 리스트 순서를 바꾸면 예상 밖 교체가 생길 수 있습니다. 안정적인 이름이 있으면 map/set 기반 `for_each`가 이해하기 쉽습니다. 키는 plan 때 결정 가능해야 하며 민감한 값을 키로 사용하지 않습니다.

다른 자원의 속성을 참조하면 보통 의존성을 자동 추론합니다. 속성 참조로 표현되지 않는 실제 순서 제약이 있을 때만 `depends_on`을 검토합니다. `depends_on`은 잘못된 입력이나 앱 준비 상태를 해결하는 만능 옵션이 아닙니다.

[for_each](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each) · [depends_on](https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on)

## 모듈·환경 분리·workspace

모듈은 `.tf` 설정의 재사용 단위입니다. 실행하는 디렉터리가 root module, `module` 블록으로 호출하는 구성이 child module입니다.

```hcl
module "network" {
  source      = "../../modules/network"
  environment = var.environment
  vpc_cidr    = "10.20.0.0/16"
}
```

이 코드는 입력 변수를 갖춘 `modules/network`가 이미 있을 때의 예입니다. module의 출력은 `module.network.vpc_id`처럼 사용합니다. 재사용 코드가 같아도 Dev·Prd의 state·계정·권한·입력은 분리할 수 있습니다.

CLI workspace는 같은 구성의 state 인스턴스를 구분하는 기능입니다. `terraform workspace show`로 현재 workspace를 확인합니다. **workspace만 바꾼다고 AWS 계정·IAM 권한까지 자동 격리되지는 않습니다.** 운영 환경에는 별도 root 구성과 backend key·계정·권한 분리를 함께 고려합니다.

[모듈](https://developer.hashicorp.com/terraform/language/modules) · [CLI workspace](https://developer.hashicorp.com/terraform/cli/workspaces)

## state·lock·Git 관리

State는 `aws_instance.web` 같은 코드 주소와 실제 클라우드 자원을 연결하고 속성 정보를 보관합니다. 기본 로컬 backend에서는 `terraform.tfstate`에 저장됩니다. state만 지워도 실제 서버가 삭제되지는 않으며, 관리 연결을 잃을 수 있습니다.

| 파일 | Git에 넣을까? |
| --- | --- |
| `.tf`, 비밀 없는 예제 `.tfvars` | 코드 검토를 위해 관리 |
| `.terraform.lock.hcl` | provider 버전·검증값 재현을 위해 관리 |
| `.terraform/` | 초기화 캐시이므로 제외 |
| `*.tfstate`, `*.tfstate.*` | 민감 정보·운영 상태이므로 제외 |
| `*.tfplan`, 비밀 포함 `.tfvars` | 제외하고 별도 보호 |

**`.terraform.lock.hcl`과 state lock은 서로 다릅니다.** 전자는 의존성 잠금 파일, 후자는 같은 state의 동시 변경을 막는 장치입니다. `sensitive = true`는 출력 가림 표시이며 state에서 값을 제거하거나 암호화하는 기능이 아닙니다. 버전·provider가 지원하는 ephemeral·write-only 기능은 별도 개념입니다.

[민감한 값과 state](https://developer.hashicorp.com/terraform/language/manage-sensitive-data) · [의존성 lock 파일](https://developer.hashicorp.com/terraform/language/files/dependency-lock)

## S3 원격 backend와 상태 잠금

팀 작업에서는 state를 원격 저장소에 보관하고 잠금을 사용합니다. S3 backend 예시는 **이미 생성된 상태 보관용 버킷**이 있어야 합니다. 앱에서 만드는 일반 버킷과 초기화 순서를 구분하세요.

```hcl
terraform {
  backend "s3" {
    bucket       = "YOUR_EXISTING_STATE_BUCKET"
    key          = "study/dev/terraform.tfstate"
    region       = "ap-northeast-2"
    encrypt      = true
    use_lockfile = true
  }
}
```

`use_lockfile = true`는 Terraform 1.10 이상에서 S3 잠금 파일을 사용합니다. 현재 공식 문서에서 DynamoDB 기반 잠금은 deprecated이므로 새 구성은 S3 잠금을 기준으로 확인합니다. 필요한 state·잠금 객체 권한을 설정하고 버킷 버전 관리와 접근 제한을 구성합니다.

Backend 설정에서는 일반 입력 변수 `var.*`를 사용할 수 없습니다. 환경별 값은 부분 backend 설정과 `init -backend-config=...` 등으로 구분합니다. **state를 옮길 때의 `init -migrate-state`와 새 설정을 다시 초기화하는 `-reconfigure`는 같은 동작이 아닙니다.**

[S3 backend·잠금·권한](https://developer.hashicorp.com/terraform/language/backend/s3)

## 기존 자원 import·코드 이름 변경

기존 자원을 Terraform 관리에 편입할 때 import를 사용합니다. 다음은 **이미 존재하는 S3 버킷**에 대한 코드 예시이며 새로 만드는 연습 명령이 아닙니다.

```hcl
resource "aws_s3_bucket" "existing" {
  bucket = "YOUR_EXISTING_BUCKET"
}

import {
  to = aws_s3_bucket.existing
  id = "YOUR_EXISTING_BUCKET"
}
```

Terraform 1.5 이상에서 import 블록을 계획·적용할 수 있습니다. provider와 리소스별 import ID 형식은 다릅니다. 가져오기 전 plan에서 import 외의 변경·교체가 없는지 확인합니다. CLI `terraform import`는 기본적으로 state에 연결하는 동작이며 모든 HCL을 자동 작성하는 명령은 아닙니다.

같은 자원의 코드 이름을 바꾸는 경우에는 삭제·재생성을 유도하지 않도록 이동을 표현할 수 있습니다.

```hcl
moved {
  from = terraform_data.note
  to   = terraform_data.memo
}
```

위 블록은 기존 resource 이름도 `memo`로 변경한 상황의 예입니다. `state rm`은 실제 자원을 삭제하는 명령이 아니라 **Terraform의 관리 연결을 제거**하므로 목적을 구분합니다.

[기존 자원 import](https://developer.hashicorp.com/terraform/language/import) · [모듈 리팩터링·moved](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring)

## drift·교체·삭제를 다루는 법

Drift는 코드·state와 실제 자원 사이의 차이입니다. 콘솔·CLI로 수동 변경했다면 다음 plan에서 변경을 관찰하고 코드에 반영할지 원래 상태로 되돌릴지 결정합니다.

```bash
terraform plan -refresh-only
```

refresh-only는 실제 자원을 코드대로 수정하는 계획이 아니라 **state와 output을 실제 상태에 맞추는 계획**입니다. 적용은 state를 변경하므로 검토 후 진행합니다.

`lifecycle { prevent_destroy = true }`는 설정이 존재하는 동안 삭제를 요구하는 계획을 막는 보호 장치이며 백업이나 클라우드 전체의 삭제 방지 정책을 대신하지 않습니다. 블록을 코드에서 없애면 보호도 없어질 수 있습니다. `ignore_changes`를 넓게 사용하면 중요한 drift를 숨길 수 있습니다.

`terraform destroy`는 현재 state가 관리하는 자원을 대상으로 합니다. 삭제 전에 계정·리전·backend·workspace와 plan을 확인합니다. 실패한 apply는 이미 일부 자원을 바꿨을 수 있으며 자동으로 전체 롤백된다고 가정하지 않습니다.

[refresh-only](https://developer.hashicorp.com/terraform/tutorials/state/refresh) · [lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)

## AWS 계정 없이 하는 로컬 실습

[전체 main.tf 받기](sample-files/terraform-basics/main.tf)를 **빈 실습 폴더**에 저장하세요. Terraform 1.5 이상이면 내장 `terraform_data`로 AWS 계정·외부 provider 없이 진행할 수 있습니다. 이 파일에는 외부 명령을 실행하는 provisioner도 없습니다.

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan -out=local.tfplan
terraform show local.tfplan
terraform apply local.tfplan
terraform output
terraform state list
terraform plan -detailed-exitcode
```

첫 계획은 `terraform_data.service` 두 개를 만들고, 출력은 `api-dev`, `web-dev`를 포함합니다. 같은 입력으로 다시 plan하면 변경 없음(종료 코드 0)입니다. 변수 변경도 확인합니다.

```bash
terraform plan -var='environment=stg'
```

두 리소스의 input이 바뀌는 계획만 확인하며 위 명령은 변경을 적용하지 않습니다. 실습 종료 시 **이 실습 폴더에서** `terraform destroy`를 실행해 확인 후 로컬 관리 항목을 정리합니다. 실제 AWS 리소스를 만드는 구성의 destroy와 혼동하지 마세요.

## 오류 해결과 실무 순서

| 상황 | 점검 |
| --- | --- |
| `Initialization required` | 해당 폴더에서 init, backend 변경 여부 |
| provider 인증 오류 | 계정·프로파일·SSO 세션·provider 지원 버전 |
| `Error acquiring the state lock` | 다른 작업 진행 여부, 잘못된 동시 실행 |
| 변수 입력 요청 | tfvars 전달 여부, 변수 default·이름 |
| 예상치 못한 replace | 불변 속성 변경, count 인덱스, 주소 변경 |
| `Saved plan is stale` | state가 바뀌었으므로 다시 plan |
| apply 일부 실패 | 오류 원인·실제 자원·state 확인 후 다시 plan |

잠금 오류를 보고 무조건 `force-unlock`이나 `-lock=false`를 쓰지 않습니다. 실제 실행 중인 작업이 없는지 먼저 확인합니다. `-target`도 예외 복구용으로 검토하며 일상 배포에서 전체 의존성 검토를 대체하지 않습니다.

**반복 순서:** 코드 수정 → fmt → init/validate → plan 검토 → apply → output·서비스 동작 확인 → Git에 코드와 의존성 잠금 파일 기록.

[프로젝트 2 · Terraform 인프라 자동화](cloud-iac-reference.html) · [AWS CLI 사용법](aws-cli-reference.html) · [GitHub 기록법](github-reference.html)
