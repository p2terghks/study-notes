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

## 상세 학습 안내: 기본 사용법에서 실무까지

**Terraform을 잘 쓴다는 것은 어떤 자원이 왜 바뀌는지 plan을 설명할 수 있다는 뜻입니다.** 앞의 15개 항목은 빠른 사전이고 여기부터는 타입·함수·모듈·AWS 구성·상태 복구를 깊게 다룹니다.

|단계|학습 내용|스스로 확인할 질문|
|---|---|---|
|입문|블록, 변수, 참조, init/plan/apply|실제 서버 이름과 Terraform 주소가 어떻게 다른가?|
|문법|타입, 조건식, for, 내장 함수|함수 결과를 실행 전에 예측할 수 있는가?|
|구성|provider, 모듈, 환경 분리|의존성이 어떤 참조로 연결되는가?|
|운영|state, 잠금, import, moved, drift|삭제 없이 코드 구조를 바꿀 수 있는가?|
|팀 자동화|테스트, 계획 검토, 승인, 복구|실패 후 실제 자원과 state를 비교할 수 있는가?|

확장판 로컬 실습은 Terraform CLI **1.16.5**를 기준으로 검증합니다. CLI 버전, AWS provider 버전, module 버전은 각각 다른 의존성입니다. 필요한 최소 버전이 있는 기능은 본문에서 구분합니다.

짧은 코드는 설명용 발췌입니다. 모든 예제를 같은 폴더에 붙이면 이름 충돌이 생길 수 있습니다. 독립 실행용 파일은 마지막 ZIP을 사용하세요. 이번 작업에서 실제 AWS 리소스를 만들지는 않습니다.

## HCL 한 줄씩 읽기: 주소와 실제 이름

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = "my-unique-study-assets"
  tags = {
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
```

|부분|의미|바꿀 때 확인|
|---|---|---|
|`resource`|관리 대상 선언|일반 언어의 함수 호출이 아님|
|`aws_s3_bucket`|provider가 정의한 자원 종류|provider 버전별 인수·속성|
|`assets`|모듈 안의 논리 이름|주소 변경이므로 moved 검토|
|`bucket`|AWS에 전달할 실제 이름|이름 변경으로 교체가 필요한지|
|`tags`|문자열 map 설정|비용·환경·소유자 분류|
|`aws_s3_bucket.assets.id`|해당 자원의 ID 참조|직접 문자열 복사보다 의존성이 명확|

`aws_s3_bucket.assets`는 Terraform 주소이고 `my-unique-study-assets`는 AWS 이름입니다. 모듈 내부이면 `module.storage.aws_s3_bucket.assets`처럼 주소가 확장됩니다. 일반 목적 S3 버킷 이름은 같은 AWS partition 안에서 전역적으로 유일해야 합니다.

인수(argument)는 내가 입력하는 설정, 속성(attribute)은 provider가 제공하는 값입니다. `id`, `arn` 등은 자원별로 다르므로 무조건 존재한다고 가정하지 않습니다. 같은 폴더의 `.tf`는 함께 읽으며 파일 이름순으로 실행하지 않습니다.

## 타입 심화: list · set · map · object · tuple

|타입|의미|예|주 사용처|
|---|---|---|---|
|`string`|문자열|`"dev"`|이름·리전|
|`number`|숫자|`2`, `0.5`|개수·용량|
|`bool`|참/거짓|`true`|옵션 활성화|
|`list(string)`|동일 타입, 순서 있음|`["a", "b"]`|순서가 의미 있는 목록|
|`set(string)`|중복 없음, 인덱스 없음|`toset(["a", "a", "b"])`|식별자 집합|
|`map(number)`|문자열 키, 값 타입 동일|`{ web = 2, api = 3 }`|이름별 설정|
|`object({...})`|속성별 타입 정의|`{ name = "api", port = 8080 }`|설정 계약|
|`tuple([...])`|위치별 타입 정의|`["api", 8080, true]`|고정 구조|

```hcl
variable "services" {
  type = map(object({
    port     = number
    replicas = optional(number, 1)
    enabled  = optional(bool, true)
  }))
  default = {
    api = { port = 8080 }
    web = { port = 3000, replicas = 2 }
  }
}
```

`optional(number, 1)`은 생략한 속성에 기본값을 줍니다. api의 replicas는 1입니다. optional object 속성 기본값은 Terraform 1.3 이상 기준입니다. object 변환 과정에서 선언하지 않은 속성이 제거될 수 있으므로 입력 키 오타가 반드시 오류가 된다고 믿으면 안 됩니다.

`any`는 실제 타입을 추론하도록 하는 표시입니다. 모듈 입력에는 구체적인 object 계약을 사용하면 잘못된 값을 일찍 찾을 수 있습니다. [타입 제약](https://developer.hashicorp.com/terraform/language/expressions/type-constraints).

## null · 빈 값 · unknown의 차이

|값|의미|주의|
|---|---|---|
|`null`|값을 지정하지 않음|빈 문자열과 다름|
|`""`|길이 0의 문자열|필수 값 검사를 대신하지 못함|
|`[]`|원소가 없는 collection 표현|길이가 0이며 null은 아님|
|`{}`|속성이 없는 object/map 표현|필수 속성 타입에 맞지 않을 수 있음|
|unknown|apply 이후 확정되는 값|오류나 null이 아님|

선택 인수에 null을 주면 보통 생략한 것처럼 처리하지만 provider 스키마를 확인해야 합니다. `nullable = false`는 변수 자체의 null을 제한하며 중첩 속성의 null까지 전부 막는 것은 아닙니다.

`for_each`의 key/집합 원소는 plan 때 알아야 합니다. `{ api = aws_vpc.main.id }`는 key가 이미 알려져 있지만 `toset([aws_vpc.main.id])`는 아직 생성하지 않은 ID를 식별자로 쓰므로 문제가 될 수 있습니다.

`try(unknown, "fallback")`은 fallback을 선택하지 않습니다. try는 동적 평가 오류를 처리할 뿐 아직 모르는 값을 바꾸는 함수가 아닙니다.

## 조건식 · for 표현식 · splat 사용법

```hcl
locals {
  size = var.environment == "prod" ? 3 : 1
  enabled_names = [for name, cfg in var.services : name if cfg.enabled]
  enabled_services = {
    for name, cfg in var.services : name => cfg if cfg.enabled
  }
}
```

`조건 ? 참일 때 값 : 거짓일 때 값`의 두 결과는 호환되는 타입이어야 합니다. `for`는 새 값을 만드는 표현식이고, resource의 `for_each`는 관리 인스턴스를 나누는 메타 인수입니다. 두 개념을 구분하세요.

|표현|기능|결과 형태|
|---|---|---|
|`[for x in list : upper(x)]`|각 문자열 변환|리스트/튜플|
|`{ for k, v in map : k => v.port }`|키별 포트만 추출|object/map|
|`[for x in list : x if x != ""]`|조건에 맞는 값만 유지|필터링 목록|
|`aws_instance.web[*].id`|count 기반 항목의 id 추출|목록|
|`[for x in aws_instance.api : x.id]`|for_each 기반 map의 id 추출|목록|

마지막 두 줄은 해당 resource가 정의된 구성의 발췌입니다. map의 순회를 원래 입력 순서 보장으로 해석하지 않습니다. 복잡한 중첩 변환은 여러 local로 나누면 검토가 쉬워집니다. [표현식](https://developer.hashicorp.com/terraform/language/expressions).

## 문자열 함수: 이름·라벨 정리

빈 실습 폴더에서 `terraform console`을 실행하고 아래 식을 입력하세요. 먼저 결과를 예상한 뒤 확인하면 좋습니다.

|함수·입력|결과|목적|
|---|---|---|
|`lower("API-DEV")`|`"api-dev"`|이름 규칙 통일|
|`upper("dev")`|`"DEV"`|표시용 라벨|
|`trimspace(" dev ")`|`"dev"`|양끝 공백 제거|
|`replace("team_api", "_", "-")`|`"team-api"`|치환|
|`format("%s-%02d", "web", 3)`|`"web-03"`|번호 형식|
|`join("-", ["team", "dev", "api"])`|`"team-dev-api"`|여러 값 연결|
|`split(",", "web,api")`|`["web", "api"]`|구분자 분리|
|`startswith("prod-api", "prod-")`|`true`|접두사 검사|
|`trimprefix("env-dev", "env-")`|`"dev"`|접두사 제거|
|`substr("terraform", 0, 5)`|`"terra"`|문자열 일부|

```hcl
locals {
  prefix = lower(join("-", [var.project, var.environment]))
  name   = "${local.prefix}-api"
}
```

소문자로 바꾸었다고 AWS 이름 길이·허용 문자까지 모두 만족한 것은 아닙니다. 입력 validation도 구성합니다. 이름에 `timestamp()`를 넣으면 실행마다 변경이 발생할 수 있으므로 안정적인 자원 이름으로 적합하지 않습니다. [함수 분류](https://developer.hashicorp.com/terraform/language/functions).

## 컬렉션 함수: 태그와 목록 다루기

|함수·식|결과·동작|주의|
|---|---|---|
|`length(["web", "api"])`|2|null에는 사용 불가|
|`contains(["dev", "prod"], "dev")`|true|부분 문자열 검색은 strcontains|
|`lookup({ dev = 1 }, "prod", 2)`|2|키가 없으면 기본값|
|`merge({env="dev"}, {env="prod"})`|env=prod|뒤 map 우선|
|`concat(["a"], ["b", "a"])`|a, b, a|중복 유지|
|`distinct(["b", "a", "b"])`|b, a|첫 등장 순서 유지|
|`sort(["b", "a"])`|a, b|문자열 정렬|
|`flatten([["a"], ["b", "c"]])`|a, b, c|중첩 리스트 평탄화|
|`keys({web=2, api=1})`|api, web|키 사전순|
|`values({web=2, api=1})`|1, 2|키 정렬 순서의 값|
|`zipmap(["a","b"],[1,2])`|a=1, b=2|키·값 개수 일치 필요|
|`toset(["a","a","b"])`|a, b 집합|순서·인덱스에 의존 금지|

```hcl
locals {
  common_tags = { Project = "study", Environment = var.environment }
  tags        = merge(local.common_tags, var.extra_tags)
}
```

이 순서는 extra_tags가 Environment까지 덮어쓸 수 있습니다. 공통 값을 강제하려면 순서를 반대로 합니다. merge는 깊은 병합이 아닙니다. `merge({a={x=1}}, {a={y=2}})`는 a 전체를 대체하므로 x를 보존하지 않습니다. [merge](https://developer.hashicorp.com/terraform/language/functions/merge), [flatten](https://developer.hashicorp.com/terraform/language/functions/flatten).

## 오류·기본값 함수: try · can · coalesce

|함수|기능|예|
|---|---|---|
|`try(a, b)`|첫 번째 오류 없는 평가 결과|`try({}.name, "unnamed")` → unnamed|
|`can(expr)`|동적 평가 오류가 없는지 bool|`can(tonumber("abc"))` → false|
|`coalesce(a, b)`|첫 non-null·non-empty-string|`coalesce(null, "", "dev")` → dev|
|`coalescelist(a, b)`|첫 비어 있지 않은 목록|`coalescelist([], ["api"])`|
|`tonumber("8080")`|문자열을 숫자로|8080|
|`tostring(8080)`|숫자를 문자열로|`"8080"`|

try로 선언하지 않은 변수 참조 같은 정적 오류까지 숨길 수는 없습니다. 외부 JSON 선택 필드를 정규화하는 local에서 사용하고 모든 오류를 기본값으로 덮지 않습니다. coalesce는 모든 인수가 null/빈 문자열이면 오류이며 호환되는 타입이 필요합니다.

```hcl
variable "project" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.project))
    error_message = "3~20자, 소문자로 시작하며 소문자·숫자·하이픈만 사용하세요."
  }
}
```

regex는 일치하지 않으면 오류이므로 can으로 감싸 검사 결과를 bool로 만듭니다. regexall은 일치 목록을 반환하므로 length로 검사할 수도 있습니다. [try](https://developer.hashicorp.com/terraform/language/functions/try), [can](https://developer.hashicorp.com/terraform/language/functions/can), [coalesce](https://developer.hashicorp.com/terraform/language/functions/coalesce).

## 파일 · JSON · 템플릿 함수

|함수|기능|사용처|
|---|---|---|
|`file(path)`|기존 UTF-8 파일 읽기|정책·설정 입력|
|`templatefile(path, vars)`|템플릿에 변수 채우기|cloud-init, 앱 설정|
|`jsonencode(value)`|HCL 값 → JSON 문자열|IAM 정책·task definition|
|`jsondecode(text)`|JSON → HCL 값|외부 설정|
|`yamlencode(value)`|HCL 값 → YAML 문자열|도구 설정|
|`yamldecode(text)`|지원되는 YAML 부분집합 해석|YAML 입력|
|`filebase64(path)`|파일 바이트 base64 인코딩|바이너리 입력|
|`filesha256(path)`|내용 해시 계산|변경 감지|

```hcl
locals {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = ["${aws_s3_bucket.assets.arn}/*"]
    }]
  })
}
```

이 예제는 정책 문자열을 만들 뿐 IAM 역할에 자동 연결하지 않습니다. 직접 JSON 따옴표·쉼표를 조립하는 것보다 jsonencode가 안전합니다.

```hcl
locals {
  rendered = templatefile("${path.module}/app.conf.tftpl", {
    app_name = "study-api"
    port     = 8080
  })
}
```

`app.conf.tftpl`은 다음 텍스트 파일입니다.

```text
name=${app_name}
port=${port}
```

path.module은 현재 모듈 폴더입니다. file/templatefile은 파일 생성 순서를 관리하는 자원이 아니므로 같은 apply에서 나중에 만들어질 파일을 읽게 하지 않습니다. secret을 렌더링하면 결과와 state에 남을 수 있습니다. [templatefile](https://developer.hashicorp.com/terraform/language/functions/templatefile), [jsonencode](https://developer.hashicorp.com/terraform/language/functions/jsonencode).

## CIDR · 숫자 함수: 네트워크 계산

|식|결과|해석|
|---|---|---|
|`cidrsubnet("10.20.0.0/16", 8, 0)`|10.20.0.0/24|prefix에 8비트 추가, 0번|
|`cidrsubnet("10.20.0.0/16", 8, 1)`|10.20.1.0/24|1번 subnet|
|`cidrhost("10.20.1.0/24", 10)`|10.20.1.10|host 주소|
|`cidrsubnets("10.20.0.0/16", 8, 8)`|10.20.0.0/24, 10.20.1.0/24|연속 구간|
|`min(3, 8)` / `max(3, 8)`|3 / 8|작은 값·큰 값|
|`ceil(2.2)` / `floor(2.8)`|3 / 2|올림·내림|
|`range(3)`|0, 1, 2|반복용 숫자 목록|

newbits=8은 subnet 8개가 아니라 prefix 길이를 8 늘린다는 뜻입니다. /16을 /24로 나누면 이론상 256개 구간, 번호는 0~255입니다. 계산 성공이 AWS 예약 IP와 서비스별 subnet 크기 제한을 모두 만족한다는 뜻은 아닙니다.

이미 적용한 CIDR 순서를 바꾸면 실제 subnet 교체로 이어질 수 있습니다. 기존 할당을 보존한 채 확장합니다. [cidrsubnet](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet), [cidrsubnets](https://developer.hashicorp.com/terraform/language/functions/cidrsubnets).

## for_each 설계와 dynamic 블록

```hcl
resource "terraform_data" "service" {
  for_each = {
    for name, cfg in var.services : name => cfg if cfg.enabled
  }
  input = {
    name = each.key
    port = each.value.port
  }
}
```

each.key는 api 같은 식별자, each.value는 그 설정입니다. web을 frontend로 바꾸면 주소가 달라지므로 이름만 변경하는 것인지 삭제/생성하는 것인지 moved로 의도를 표현합니다.

|요구|방법|주의|
|---|---|---|
|동일한 항목 N개|count|인덱스가 식별자|
|이름별 서비스|map for_each|안정적인 key 사용|
|선택적 1개|count=enabled?1:0|미생성 시 `[0]` 참조 주의|
|리소스 내부 블록 반복|dynamic|provider가 지원하는 중첩 블록만|
|값 변환|for 표현식|자원을 생성하지 않음|

AWS SG 내부 ingress 반복의 발췌입니다. vpc_id와 allowed_cidrs 입력 선언이 필요합니다.

```hcl
resource "aws_security_group" "web" {
  name   = "study-web"
  vpc_id = var.vpc_id
  dynamic "ingress" {
    for_each = toset([80, 443])
    iterator = rule
    content {
      from_port   = rule.value
      to_port     = rule.value
      protocol    = "tcp"
      cidr_blocks = var.allowed_cidrs
    }
  }
}
```

dynamic은 lifecycle 같은 메타 블록을 만들 수 없습니다. SG 규칙을 별도 aws_vpc_security_group_ingress_rule로 관리할 수도 있지만 같은 규칙을 inline과 별도 자원으로 중복 관리하지 않습니다. [dynamic](https://developer.hashicorp.com/terraform/language/expressions/dynamic-blocks).

## 의존성 그래프와 병렬 실행

```hcl
resource "aws_subnet" "app" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.20.1.0/24"
  availability_zone = "ap-northeast-2a"
}
```

aws_vpc.main.id 참조로 VPC → subnet 의존성을 알 수 있습니다. 파일 이름의 01, 02가 순서를 지정하는 것은 아닙니다. 독립적인 자원은 병렬로 처리합니다.

|상황|접근|
|---|---|
|다른 자원 ID 필요|직접 속성 참조|
|참조 없는 실제 선행 조건|최소 범위 depends_on 검토|
|상호 참조 Cycle|별도 rule/attachment로 관계 분리|
|API rate limit|재시도·구성 분리·parallelism 검토|
|서버 생성 후 앱 미준비|배포·헬스체크에서 확인|

module 전체에 depends_on을 붙이면 보수적 계획과 unknown 값이 늘 수 있습니다. 서버가 생성됐다는 것과 애플리케이션이 정상 응답한다는 것은 다릅니다.

## lifecycle: 교체·삭제 보호의 한계

|옵션|기능|한계|
|---|---|---|
|create_before_destroy|새 자원 먼저 생성|이름 충돌·quota·여유 용량 필요|
|prevent_destroy|규칙이 있는 동안 파괴적 계획 거부|resource 블록 삭제 시 보호도 사라짐|
|ignore_changes|갱신 계획에서 지정 속성 무시|잘못된 설정도 놓칠 수 있음|
|replace_triggered_by|다른 관리 대상 변경으로 교체|일반 변수 값을 직접 넣는 용도 아님|

```hcl
resource "terraform_data" "release" {
  triggers_replace = var.release_version
}
```

값 기반 교체 기준을 관리할 때 terraform_data를 사용할 수 있습니다. 변경 시 교체가 정말 필요한지 먼저 판단합니다. prevent_destroy는 AWS 콘솔이나 다른 도구의 삭제를 막지 않으며 중요한 데이터에는 서비스 삭제 보호·백업·IAM도 필요합니다.

ECS 앱 배포처럼 다른 도구가 담당하는 속성만 명확히 분리합니다. ignore_changes=all로 계획을 조용하게 만들면 실제 관리 책임도 사라질 수 있습니다. [lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle).

## validation · precondition · postcondition · check

|검사|목적|실패 결과|
|---|---|---|
|variable validation|입력 계약|잘못된 입력 차단|
|precondition|작업 선행 조건|확인되는 시점에 관련 작업 차단|
|postcondition|결과 조건|이미 만든 자원이 자동 롤백되지는 않음|
|check|독립적인 상태 점검|일반 plan/apply에서는 경고, 배포 게이트로 착각 금지|
|test assert|테스트 기대 결과|테스트 실패|

```hcl
resource "terraform_data" "settings" {
  input = var.replicas
  lifecycle {
    precondition {
      condition     = var.environment != "prod" || var.replicas >= 2
      error_message = "prod는 replicas가 2 이상이어야 합니다."
    }
  }
}
```

unknown 때문에 일부 검사는 apply 시점으로 미뤄질 수 있습니다. 입력·출력 계약을 나누고 어느 단계에서 실패해야 하는지 결정하세요. [사용자 정의 조건](https://developer.hashicorp.com/terraform/language/expressions/custom-conditions).

## 모듈 설계: 입력 → 내부 자원 → 출력

```text
infra/
  environments/dev/main.tf
  environments/prod/main.tf
  modules/service-contract/
    main.tf
    variables.tf
    outputs.tf
```

child module에서 variable을 선언하고 root에서 전달합니다. root의 var.environment가 child로 자동 전달되지는 않습니다.

```hcl
module "api" {
  source       = "../../modules/service-contract"
  environment  = "dev"
  service_name = "api"
  port         = 8080
}
output "api_config" {
  value = module.api.config
}
```

이 발췌는 해당 입력과 config output을 가진 child module이 필요합니다. 다운로드에는 실제 모듈 실습을 제공합니다.

|설계|기준|
|---|---|
|입력|바뀌는 값만 공개, 타입·설명·validation|
|출력|소비자가 필요한 ID·ARN·계약만 노출|
|크기|함께 변경되는 자원 단위|
|예제|최소 호출 예·테스트 포함|
|호환성|입력 삭제·주소 변경·타입 변경을 기록|
|버전|Registry는 version, Git source는 ref 고정|

Registry module의 version과 provider version은 다릅니다. `.terraform.lock.hcl`은 원격 module 버전을 잠그는 파일이 아닙니다. provider 설정은 보통 root에서 관리하여 child에 전달합니다. [모듈 개발](https://developer.hashicorp.com/terraform/language/modules/develop).

## provider alias로 여러 리전·계정 연결

```hcl
provider "aws" {
  region = "ap-northeast-2"
}
provider "aws" {
  alias  = "virginia"
  region = "us-east-1"
}
resource "aws_s3_bucket" "secondary" {
  provider      = aws.virginia
  bucket_prefix = "study-secondary-"
}
```

alias는 provider 설정의 별칭이며 AWS 이름 suffix가 아닙니다. 다른 계정은 assume role 등의 인증도 별도로 필요합니다. provider 두 개를 선언했다고 모든 자원이 양쪽에 복제되지는 않습니다.

```hcl
module "secondary" {
  source = "../../modules/storage"
  providers = {
    aws = aws.virginia
  }
}
```

storage 모듈이 있을 때 적용하는 발췌입니다. child가 내부에서 alias를 직접 쓰면 required_providers의 configuration_aliases도 선언합니다. state 자원이 참조하는 provider 설정은 자원 이전/정리 전에 제거하지 않습니다. [provider 설정](https://developer.hashicorp.com/terraform/language/providers/configuration).

## AWS 예제: 비공개 S3 버킷 전체 구성

ZIP의 aws-storage/main.tf는 버전·provider 설정까지 포함합니다. 아래는 핵심 자원입니다. state backend용 버킷과 앱 저장용 버킷은 목적을 분리합니다.

```hcl
resource "aws_s3_bucket" "assets" {
  bucket_prefix = "study-assets-"
  force_destroy = false
  tags = {
    Project     = "terraform-study"
    Environment = "dev"
  }
}
resource "aws_s3_bucket_public_access_block" "assets" {
  bucket                  = aws_s3_bucket.assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

bucket_prefix로 유일한 suffix를 붙입니다. force_destroy=false이면 내용이 남은 버킷을 자동 비우기 하지 않습니다. 버전 관리로 이전 데이터 복구를 도울 수 있지만 과거 객체도 저장 비용을 차지합니다.

AWS 적용은 예상 계정·IAM·SCP·리전을 확인하고 plan을 검토한 뒤 진행합니다. 이 문서에서는 실제 AWS 적용을 수행하지 않았습니다. [S3 provider 문서](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket).

## backend 실무: bootstrap · 이전 · 권한

backend는 일반 자원보다 먼저 초기화됩니다. 같은 root에서 state 버킷을 만들면서 최초 init부터 그 버킷을 쓰려면 순환 문제가 생기므로 별도 bootstrap 또는 기존 버킷이 필요합니다.

```hcl
# backend.tf
terraform {
  backend "s3" {}
}
```

```text
# dev.s3.tfbackend: 비밀키를 넣지 않음
bucket       = "EXISTING_STATE_BUCKET"
key          = "team/dev/terraform.tfstate"
region       = "ap-northeast-2"
encrypt      = true
use_lockfile = true
```

```bash
terraform init -backend-config=dev.s3.tfbackend
# 기존 local state를 옮기는 경우에만 검토 후 사용
terraform init -migrate-state -backend-config=dev.s3.tfbackend
```

migrate-state는 상태 이전 흐름입니다. reconfigure는 저장된 backend 설정을 다시 구성하며 상태 이전 대체 명령이 아닙니다. 혼동하면 빈 state로 기존 자원을 중복 생성하려 할 수 있습니다.

state 객체의 읽기/쓰기, `.tflock`의 읽기/쓰기/삭제, 버킷 목록 권한을 구분합니다. KMS를 쓰면 키 정책도 필요합니다. dev/prod key만 나눠도 같은 역할이 모두 접근하면 권한 격리는 아닙니다. [S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3).

## import: 기존 자원을 관리 대상으로 가져오기

import는 기존 자원 ID와 Terraform 주소를 연결합니다. 먼저 다른 state가 이미 관리하는지 확인합니다.

```hcl
resource "aws_s3_bucket" "legacy" {
  bucket = "EXISTING_BUCKET_NAME"
}
import {
  to = aws_s3_bucket.legacy
  id = "EXISTING_BUCKET_NAME"
}
```

1.5 이상 import block으로 계획에 포함할 수 있습니다. plan에서 import 외 원치 않는 변경·교체가 없는지 확인합니다. 버킷 import 하나가 versioning·policy·public access block까지 모두 연결해 주는 것은 아닙니다.

```bash
# resource 선언을 준비한 후 명령형으로 연결하는 대안
terraform import aws_s3_bucket.legacy EXISTING_BUCKET_NAME
terraform plan
```

명령형 import는 즉시 state를 바꿉니다. 기존 설정을 완벽한 HCL로 만들어 주는 명령은 아닙니다. import block과 plan의 generate-config-out 옵션으로 설정을 생성하더라도 기본값·중복·조직 정책을 직접 정리해야 합니다. [Import](https://developer.hashicorp.com/terraform/language/import).

## moved · removed: 실제 삭제 없이 구조 바꾸기

```hcl
moved {
  from = terraform_data.old
  to   = terraform_data.service
}
```

moved는 1.1 이상에서 주소 이전을 선언합니다. 실제 AWS 이름을 바꾸지 않습니다. 모든 환경과 module 사용자의 이전을 고려해 기록을 유지합니다.

```hcl
# 1.7 이상: 실제 자원은 남기고 관리 연결만 제거
removed {
  from = aws_s3_bucket.legacy
  lifecycle {
    destroy = false
  }
}
```

removed는 기존 resource 선언을 제거하는 변경과 함께 검토합니다. 이후 그 자원은 해당 state의 관리 밖으로 나가므로 새 담당자와 운영 절차가 필요합니다.

|작업|검토|
|---|---|
|논리 이름 변경|moved, 불필요 생성·삭제 없는지|
|root → module|새 module 주소로 이전|
|count → for_each|각 이전 인덱스와 새 key 매핑|
|관리만 종료|removed destroy=false 또는 통제된 state rm|

[리팩터링](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring), [관리 대상 제거](https://developer.hashicorp.com/terraform/language/state/remove).

## state 조사·복구와 부분 실패

|명령|목적|주의|
|---|---|---|
|state list|관리 주소 목록|읽기|
|state show '주소'|저장 속성 확인|비밀 출력 주의|
|state pull|state JSON 추출|파일 접근 보호|
|state mv '이전' '새주소'|주소 즉시 이전|state 변경|
|state rm '주소'|관리 연결 제거|실제 자원 유지|
|force-unlock LOCK_ID|남은 잠금 해제|진행 중 작업이 없는지 확인|
|plan -refresh-only|외부 변경을 state에 반영할 계획|계획만|
|apply -refresh-only|외부 변경을 state에 반영|코드대로 인프라 복원하는 기능 아님|

apply 실패 시 자동 전체 롤백을 가정하지 않습니다. VPC 생성 후 subnet이 실패했다면 VPC가 남을 수 있습니다. 로그 → 실제 자원 → state → 원인 수정 → 새 plan 순서로 확인하세요.

state 저장 실패 시 복구 안내와 임시 state를 먼저 보존합니다. 임의로 빈 state나 오래된 백업을 덮지 않습니다. 수동 push는 lineage·serial·최신 변경을 확인해야 하는 복구 작업입니다. state 버전 복원은 실제 인프라를 과거 상태로 복원하는 것과 다릅니다.

## sensitive · ephemeral · write-only 구분

|기능|보호 범위|한계|
|---|---|---|
|sensitive=true|일반 출력에서 값 가림|state/plan 저장될 수 있음|
|ephemeral|지원 문맥에서 plan/state 미보관|1.10+와 사용 위치 제약|
|write-only 인수|provider에 쓰되 값 미보관|1.11+와 해당 자원 지원 필요|
|외부 secret 저장소|접근 통제·회전|일반 인수로 읽으면 state에 다시 남을 수 있음|

```hcl
variable "api_token" {
  type      = string
  sensitive = true
  ephemeral = true
}
```

이 선언을 모든 resource 인수에 전달할 수 있는 것은 아닙니다. 영속 식별자나 일반 output에서 ephemeral을 써 저장을 회피할 수 없습니다.

output -raw/-json, plan JSON, debug 로그는 민감 값을 드러낼 수 있습니다. artifact 보관 기간·다운로드 권한을 제한합니다. 코드에서 키를 지워도 기존 state snapshot·Git 이력·로그에서 자동 제거되지 않습니다. [민감 데이터](https://developer.hashicorp.com/terraform/language/manage-sensitive-data).

## 테스트: fmt · validate · test · 실제 동작

|검증|알아내는 것|한계|
|---|---|---|
|fmt|표준 서식|권한·설계 검사 아님|
|validate|구문·타입·참조|실제 계정·quota 보장 아님|
|test plan|입력과 계획의 기대값|실제 서비스 확인 아님|
|mock_provider|API 없이 module 계약|AWS 실제 동작 대체 불가|
|격리 apply|자원 생성·연결|부하·장애 전체 보장 아님|
|업무 smoke|사용자 경로|장기 안정성 별도|

현재 test 프레임워크는 1.6 이상, provider mocking은 1.7 이상 기준입니다. **run의 기본 command는 apply**이므로 AWS 구성에서 무심코 test하면 자원을 만들 수 있습니다. 계획만 필요하면 command=plan을 명시합니다.

```hcl
run "default_contract" {
  command = plan
  assert {
    condition     = output.service_count == 2
    error_message = "활성 서비스는 2개여야 합니다."
  }
}
```

이 코드는 해당 output이 있는 모듈의 tests/contract.tftest.hcl에 둡니다. test는 별도 테스트 state를 쓰고 정리를 시도하지만 실패 시 잔여 자원을 조사해야 합니다. 이번 ZIP local-contract는 외부 provider·provisioner 없이 terraform_data만 사용합니다. [Tests](https://developer.hashicorp.com/terraform/language/tests).

## Terraform CI/CD와 종료 코드 처리

```text
PR → fmt → init → validate → test → 신뢰하는 권한 환경에서 plan
                                    ↓ 변경 검토·정책 검사
main 확정 commit → 최종 plan → 환경 승인 → 같은 plan apply → 검증
```

fork PR의 임의 코드를 운영 AWS 권한으로 실행하지 않습니다. plan 권한도 state와 data source를 읽으므로 민감할 수 있습니다. OIDC의 저장소·환경 subject와 역할을 제한합니다.

```bash
#!/usr/bin/env bash
set -euo pipefail
terraform init -input=false -lockfile=readonly
terraform validate
code=0
terraform plan -input=false -lock-timeout=5m \
  -detailed-exitcode -out=review.tfplan || code=$?
case "$code" in
  0) echo '변경 없음' ;;
  2) echo '변경 있음: 계획 검토와 승인 필요' ;;
  *) echo '계획 실패' >&2; exit "$code" ;;
esac
```

lockfile이 사전에 생성·검토·커밋된 root의 예입니다. 같은 backend key의 작업끼리 concurrency를 묶고 진행 중 apply를 새 push 때문에 취소하지 않습니다. plan과 commit SHA·환경·provider 버전·artifact 무결성을 연결합니다. 저장 plan apply는 추가 yes 없이 적용됨을 기억하세요.

Terraform과 앱 CD가 ECS task definition 같은 속성을 동시에 바꾸면 충돌합니다. 소유권을 나누고 필요한 속성에 한해 ignore_changes 등을 검토합니다. [전체 CI/CD 가이드](devops-handbook-reference.html).

## 실무 변경 시나리오와 검토 기준

|요청|코드 변경|plan 확인|적용 후|
|---|---|---|---|
|태그 추가|tags/map|제자리 갱신인지|누락·비용 태그|
|subnet 추가|안정적인 key|기존 subnet 교체 없는지|라우트·AZ·SG|
|서버 크기 변경|instance_type 등|정지·교체 여부|앱·비용·메트릭|
|module 분리|module + moved|불필요 생성·삭제 없는지|output 소비자|
|기존 자원 인수|resource + import|import 외 변경|중복 관리 없는지|
|provider 갱신|제약·lockfile|대량 diff·deprecated|회귀 검증|
|관리 종료|removed|실제 삭제 아닌지|새 소유자|

PR에는 목적, 대상 계정·환경, 교체·삭제 여부, 데이터 보존, 테스트, 실패 시 복구 절차를 적습니다. plan의 0 to destroy만으로 무중단을 확정하지 말고 실제 서비스 영향을 읽으세요.

적용 전에는 workspace, 계정, backend key, 변수, commit, lockfile, plan 최신성을 확인합니다. 적용 후에는 output뿐 아니라 API·로그·DB 연결·알람을 확인합니다.

## 오류별 원인과 해결 순서

|오류·증상|흔한 원인|해결 접근|
|---|---|---|
|Unsupported argument|버전/블록 위치 불일치|설치된 provider 문서 확인|
|undeclared resource|이름 오타·다른 module 직접 참조|주소·output 확인|
|Invalid for_each argument|unknown key·잘못된 타입|고정 key map 설계|
|Invalid index|빈 count·없는 key|입력 계약·분기|
|조건식 타입 불일치|양쪽 구조가 다름|명시적 타입 통일|
|Cycle|상호 참조|rule/attachment 분리|
|Provider configuration not present|참조 provider 제거|기존 설정 복구 후 이전|
|Resource already exists|자원은 있으나 state 연결 없음|중복 생성 대신 import 검토|
|Saved plan is stale|계획 후 state 변경|새 plan·재검토|
|권한 오류|IAM·SCP·세션|실행 주체·거부 작업 확인|
|예상치 않은 대량 삭제|잘못된 환경·변수|apply 중단, 대상 비교|

TF_LOG 진단 로그는 요청 정보나 비밀이 포함될 수 있어 필요한 범위에서만 사용합니다. 오류를 숨기거나 모든 자원에 ignore_changes를 붙여 해결하지 않습니다.

## 상세 실습 ZIP과 학습 과제

[Terraform 상세 실습 ZIP 다운로드](sample-files/terraform-detailed.zip)

|폴더|내용|실행 특성|
|---|---|---|
|local-contract|타입, 함수, for_each, child module, output|AWS 계정·외부 provider 없이 실행|
|local-contract/tests|기본값·환경 변경·잘못된 입력 검증|plan 기반|
|aws-storage|비공개 S3 버킷 전체 구성|실제 적용은 AWS 자원 변경 가능|
|README.md|폴더별 실행과 예상 결과|실습별로 별도 실행|

```bash
# 압축 해제 후 local-contract 안에서
terraform init -input=false
terraform fmt -check -recursive
terraform validate
terraform test
terraform plan -out=local.tfplan
terraform show local.tfplan
terraform apply local.tfplan
terraform output
terraform plan -detailed-exitcode
```

기본 활성 서비스는 api/web 2개이고 CIDR은 10.20.0.0/24, 10.20.1.0/24입니다. 같은 입력으로 재계획하면 종료 코드 0입니다. prod 입력으로 plan하면 환경·이름 변경을 볼 수 있습니다.

과제: api 포트 변경 → worker 추가 → web 비활성화 → 이름 변경과 moved 설명 → 잘못된 port가 validation에서 차단되는지 확인. 종료 시 local-contract에서만 terraform destroy로 로컬 관리 항목을 정리합니다.

확장판 확인일 **2026-10-13**. ZIP의 VERIFICATION.md에 검증 범위를 기록합니다. AWS 실제 배포·과금 테스트는 수행하지 않았습니다.
