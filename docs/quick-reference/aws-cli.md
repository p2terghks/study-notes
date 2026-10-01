# AWS CLI 사용법

## AWS CLI는 무엇인가?

**AWS CLI는 터미널에서 AWS 서비스 API를 호출하는 도구입니다.** 콘솔에서 클릭하던 조회·설정·업로드 작업을 명령어로 실행하고 반복 작업을 스크립트로 묶을 수 있습니다. 명령을 실행할 권한은 로그인한 IAM 사용자·역할의 권한으로 결정됩니다.

```text
내 터미널 → AWS CLI → 자격 증명으로 요청 서명 → AWS API → JSON 등으로 결과 출력
```

AWS CLI는 단일 작업·조회·운영 자동화에, Terraform은 원하는 인프라 상태를 코드와 state로 관리하는 데 주로 씁니다. CLI로 Terraform 관리 리소스를 바꾸면 코드와 실제 상태가 달라지는 drift가 생길 수 있습니다.

이 문서는 **AWS CLI v2** 기준입니다. 예제의 `study`는 로컬 프로파일 이름, `ap-northeast-2`는 서울 리전입니다. 버킷·인스턴스·함수 이름은 실제 학습 환경 값으로 바꿔야 합니다. 여러 줄 명령은 macOS/Linux의 bash·zsh 기준이며 PowerShell에서는 한 줄로 합쳐 실행하면 편합니다.

## 설치와 버전 확인

| 환경 | 설치 방법 |
| --- | --- |
| macOS | 공식 AWS CLI v2 PKG 설치 프로그램 실행 |
| Windows | 공식 AWS CLI v2 MSI 설치 프로그램 실행 |
| Linux | CPU 아키텍처에 맞는 공식 v2 ZIP 설치 절차 사용 |

공식 설치 페이지에서 OS·CPU에 맞는 파일을 고르세요. `pip install awscli`는 v1 설치 경로이므로 v2 설치와 혼동하지 않습니다.

```bash
aws --version
aws help
aws ec2 help
aws ec2 describe-instances help
```

`aws-cli/2...`이면 v2입니다. 도움말이나 출력이 별도 페이지에 열리면 보통 `q`로 종료합니다. `command not found`라면 새 터미널을 열고 설치 위치와 PATH를 확인합니다.

[공식 설치·업데이트](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) · [CLI 명령어 설명서](https://docs.aws.amazon.com/cli/latest/reference/)

## 인증 방법 선택: SSO·브라우저 로그인·역할

| 사용 환경 | 기본 접근 |
| --- | --- |
| 조직의 IAM Identity Center 사용 | `aws configure sso` → `aws sso login` |
| 콘솔 자격 증명으로 로컬 개발 | 지원 환경에서 `aws login` |
| EC2·ECS 등 AWS 내부 프로그램 | 실행 환경에 연결된 IAM 역할의 임시 자격 증명 |
| GitHub Actions 등 CI | OIDC와 IAM 역할 등으로 임시 자격 증명 획득 |
| 발급된 액세스 키를 써야 하는 환경 | 별도 프로파일에 설정하고 노출·만료 관리 |

로그인은 신원을 확인하는 과정이고, API 사용 가능 여부는 IAM 정책 등 권한 평가로 결정됩니다. 로그인 성공이 관리자 권한을 뜻하지 않습니다. 로컬 학습에서도 일상 작업에 필요한 IAM 사용자·역할을 사용하고 루트 계정의 장기 액세스 키는 만들지 않습니다.

[인증 방식 공식 안내](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-authentication.html)

## IAM Identity Center로 로그인하기

조직에서 제공한 시작 URL, SSO 리전, 사용할 AWS 계정과 역할이 필요합니다. CLI 명령만 실행한다고 Identity Center나 접근 권한이 자동 생성되지는 않습니다.

```bash
aws configure sso --profile study
aws sso login --profile study
aws sts get-caller-identity --profile study
```

설정 과정에서 세션 이름·시작 URL·SSO 리전·계정·역할·기본 서비스 리전·출력 형식을 고릅니다. **SSO 리전은 Identity Center가 있는 곳이며, EC2를 사용할 리전과 다를 수 있습니다.** 기본 서비스 리전 예시는 `ap-northeast-2`, 출력 형식은 `json`입니다.

브라우저 없는 환경에서 지원되는 기기 코드 흐름은 다음과 같습니다. 본인이 시작한 로그인 요청의 코드를 사용합니다.

```bash
aws sso login --profile study --use-device-code
```

세션이 만료되면 `aws sso login`을 다시 실행합니다. `aws sso logout`은 캐시된 SSO 자격 증명을 정리하며 여러 SSO 프로파일에 영향을 줄 수 있습니다.

[SSO 설정과 로그인](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)

## 콘솔 계정으로 aws login 사용하기

최소 CLI **2.32.0** 이상에서 지원되는 브라우저 로그인 방식입니다. IAM 사용자·역할은 `SignInLocalDevelopmentAccess` 등 필요한 로그인 권한이 있어야 합니다. Identity Center 사용자라면 앞의 SSO 방식을 사용합니다.

```bash
aws login --profile study-console
aws sts get-caller-identity --profile study-console
aws logout --profile study-console
```

`study-console`은 SSO 예제와 구분한 프로파일 이름입니다. 이 방식을 선택했다면 이후 예제의 `--profile study`를 `--profile study-console`로 바꾸세요. `aws login`은 장기 키를 직접 복사하는 대신 임시 자격 증명을 얻고 관리합니다. 지원 여부는 CLI 버전과 조직 정책에 따라 달라집니다.

[aws login 공식 설명](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)

## 프로파일·리전·설정 파일

프로파일은 **자격 증명·리전·출력 설정을 고르는 이름**입니다. 프로파일 이름 자체가 AWS 계정이나 IAM 역할을 생성하지 않습니다.

```bash
aws configure list-profiles
aws configure list --profile study
aws configure set region ap-northeast-2 --profile study
aws configure set output json --profile study
aws sts get-caller-identity --profile study --no-cli-pager
```

`get-caller-identity`의 `Account`와 `Arn`으로 현재 작업 대상을 확인합니다. `configure list`는 실제 적용된 설정과 출처를 찾는 데 유용합니다.

| 파일 | 주 역할 |
| --- | --- |
| `~/.aws/config` | 리전·출력·SSO·역할 등 설정, 이름 있는 항목은 `[profile study]` |
| `~/.aws/credentials` | 키 기반 자격 증명, 이름 있는 항목은 `[study]` |
| Windows | 홈 경로를 `%USERPROFILE%`로 읽으면 됨 |

이미 발급된 키를 써야 한다면 `aws configure --profile study-key`로 입력합니다. 임시 자격 증명에는 세션 토큰도 필요합니다. 비밀 키·세션 토큰·SSO 캐시를 문서나 Git에 넣지 마세요.

리전·출력 같은 옵션은 명령행 지정이 환경 변수·파일 설정보다 우선합니다. 자격 증명은 프로파일 종류와 여러 공급자의 우선순위가 있으므로, 예상과 다른 계정으로 실행되면 `configure list`와 `get-caller-identity`로 확인합니다.

[설정 파일과 프로파일](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)

## 명령어 구조와 자주 쓰는 옵션

```bash
aws ec2 describe-instances --profile study --region ap-northeast-2 --output table --no-cli-pager
```

| 부분 | 의미 |
| --- | --- |
| `aws` | 실행 프로그램 |
| `ec2` | 서비스 |
| `describe-instances` | 수행할 작업 |
| `--profile study` | 사용할 프로파일 |
| `--region ap-northeast-2` | 조회·작업할 리전 |
| `--output json / table / text` | 출력 형식 |
| `--query '...'` | JMESPath로 응답 필드·조건 선택 |
| `--no-cli-pager` | 결과를 페이지 프로그램 없이 바로 출력 |

`--no-cli-pager`와 `--no-paginate`는 다릅니다. 전자는 화면 출력 방식, 후자는 여러 API 응답 페이지를 자동으로 가져올지의 설정입니다.

## 조회 결과 줄이기: filters와 query

```bash
aws ec2 describe-instances \
  --profile study --region ap-northeast-2 \
  --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name,IP:PrivateIpAddress}' \
  --output table --no-cli-pager
```

`--filters`는 해당 API가 지원하는 조건을 AWS 서비스 쪽에서 적용합니다. `--query`는 반환된 응답을 CLI 쪽에서 가공합니다. 모든 서비스가 같은 `--filters` 문법을 제공하는 것은 아닙니다.

응답 전체 구조를 모르면 우선 `--output json`으로 보고 필요한 필드를 선택합니다. 위 예제의 `Reservations[].Instances[]`는 중첩 배열을 펼치고 `{ID:InstanceId,...}`는 출력 이름을 붙입니다. JSON 출력은 페이지를 모아 질의하는 반면 text 출력은 페이지별 질의가 적용될 수 있어 전체 개수·최솟값 같은 계산 시 주의합니다.

[JMESPath·서버/클라이언트 필터](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html)

## S3 파일 목록·복사·동기화

`aws s3`는 파일 작업을 간단히 표현하는 고수준 명령이고, `aws s3api`는 S3 API의 세부 기능을 다룹니다. 아래 버킷은 예시이며 먼저 자신의 버킷으로 바꿉니다.

```bash
# 조회: 버킷 목록과 특정 경로의 객체
aws s3 ls --profile study
aws s3 ls s3://YOUR_BUCKET/notes/ --profile study

# 다운로드: 로컬 파일을 생성하거나 덮어쓸 수 있음
aws s3 cp s3://YOUR_BUCKET/notes/hello.txt ./downloaded-hello.txt --profile study

# 업로드: S3 객체를 생성하거나 같은 키의 객체를 갱신
aws s3 cp ./hello.txt s3://YOUR_BUCKET/notes/hello.txt --profile study

# 업로드할 변경 사항 미리 보기
aws s3 sync ./notes/ s3://YOUR_BUCKET/notes/ --dryrun --profile study
```

`sync`는 복사할 차이를 계산합니다. 마지막 명령에서 `--dryrun`을 제거하면 실제 변경이 일어납니다. `--delete`를 추가하면 소스에 없는 대상 파일도 지워질 수 있으므로 기본 예제에는 넣지 않았습니다. S3 API 요청·저장·전송에는 사용 조건에 따른 비용이 있습니다.

[S3 sync 옵션](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html)

## EC2 조회와 실행 상태 확인

```bash
# 리전 내 인스턴스 상태 조회
aws ec2 describe-instances \
  --profile study --region ap-northeast-2 \
  --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name}' \
  --output table --no-cli-pager

# 권한 검사 예시: 실제 시작하지 않음. ID는 자신의 학습용 값으로 교체
aws ec2 start-instances \
  --instance-ids i-0123456789abcdef0 \
  --dry-run --profile study --region ap-northeast-2
```

EC2의 `--dry-run`은 권한이 있으면 `DryRunOperation`, 없으면 `UnauthorizedOperation`을 반환하는 방식입니다. 권한 확인 성공도 일반적인 종료 코드 0으로 처리되지 않을 수 있습니다. 모든 작업의 실제 성공이나 용량 확보를 보장하지 않습니다.

실제 시작은 `--dry-run`을 제거하면 됩니다. 실행 중 컴퓨팅 요금이 발생할 수 있고, 중지 후에도 EBS 등 관련 자원 비용이 남을 수 있습니다. `stop`은 중지, `terminate`는 종료·삭제 의미이므로 구분합니다.

```bash
# 이미 시작한 인스턴스가 running 상태에 도달할 때까지 조회하며 대기
aws ec2 wait instance-running \
  --instance-ids i-0123456789abcdef0 \
  --profile study --region ap-northeast-2
```

waiter는 상태만 기다리며 시작 명령을 대신 실행하지 않습니다. OS나 웹앱까지 준비되었다는 보장도 아닙니다.

[EC2 start-instances](https://docs.aws.amazon.com/cli/latest/reference/ec2/start-instances.html)

## CloudWatch Logs·Lambda·CloudFormation

```bash
# 최근 10분의 로그를 보고 이후 로그 계속 관찰: Ctrl+C로 종료
aws logs tail /aws/lambda/YOUR_FUNCTION \
  --since 10m --follow --profile study --region ap-northeast-2

# Lambda 함수 목록 조회
aws lambda list-functions \
  --query 'Functions[].{Name:FunctionName,Runtime:Runtime}' \
  --output table --profile study --region ap-northeast-2 --no-cli-pager

# CloudFormation 스택 출력 조회
aws cloudformation describe-stacks --stack-name YOUR_STACK \
  --query 'Stacks[0].Outputs' --output table \
  --profile study --region ap-northeast-2 --no-cli-pager
```

Lambda 호출은 함수의 코드를 실제로 실행하므로 데이터 변경·외부 요청이 일어날 수 있습니다. 아래는 자신의 실습 함수와 `event.json`이 준비된 경우의 실행 예입니다.

```bash
aws lambda invoke --function-name YOUR_FUNCTION \
  --cli-binary-format raw-in-base64-out --payload file://event.json \
  --profile study --region ap-northeast-2 response.json
```

CLI 호출 성공만 보지 말고 응답의 `FunctionError`와 `response.json`도 확인합니다. HTTP 상태 200이어도 함수 실행이 실패했을 수 있습니다.

[로그 tail](https://docs.aws.amazon.com/cli/latest/reference/logs/tail.html) · [Lambda invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)

## 페이지네이션과 대량 결과

| 옵션 | 역할 |
| --- | --- |
| `--page-size` | 서비스 API 호출 한 번당 요청할 항목 수 조정 |
| `--max-items` | CLI가 반환할 전체 항목 수 제한 |
| `--starting-token` | 이전 CLI 응답의 다음 토큰으로 이어서 조회 |
| `--no-paginate` | 첫 API 응답 페이지만 조회 |

해당 명령이 페이지네이션을 지원하는지 도움말에서 확인합니다. 다음 예시는 최대 20개 반환이고, 계정에 함수가 더 있으면 다음 토큰을 확인합니다.

```bash
aws lambda list-functions --max-items 20 --output json \
  --profile study --region ap-northeast-2 --no-cli-pager
```

`--page-size 20`만으로 전체 출력이 20개로 제한되지는 않습니다. 페이지 토큰은 서비스의 토큰과 CLI의 토큰을 임의로 섞지 말고 해당 옵션 설명대로 사용합니다.

[페이지네이션 공식 안내](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html)

## JSON 파일 입력과 실행 전 확인

```bash
# 입력 구조만 출력: AWS API 요청 없이 템플릿 생성
aws ec2 describe-instances --generate-cli-skeleton input > describe-input.json

# 템플릿을 필요한 값으로 편집한 후 실제 조회
aws ec2 describe-instances --cli-input-json file://describe-input.json \
  --profile study --region ap-northeast-2 --no-cli-pager
```

생성된 예제 값은 그대로 실행하기 위한 실제 리소스 값이 아닙니다. 불필요한 필드는 제거하고 채워야 합니다. skeleton 형식은 CLI 버전에 따라 바뀔 수 있습니다.

| 표현 | 적용 범위 |
| --- | --- |
| S3의 `--dryrun` | 파일 작업 예정 사항 표시 |
| EC2의 `--dry-run` | 지원 API의 권한 검사 |
| `--generate-cli-skeleton input` | 로컬 입력 템플릿 생성 |
| Terraform `plan` | Terraform 설정·state·실제 자원 간 변경 계획 |

철자와 목적이 다르며 **모든 AWS 명령에 공통인 dry-run 옵션은 없습니다.**

[JSON·YAML 입력과 skeleton](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-skeleton.html)

## 자주 만나는 오류

| 메시지·증상 | 먼저 확인할 것 |
| --- | --- |
| `Unable to locate credentials` | 프로파일 선택과 해당 방식의 로그인 |
| `ExpiredToken` | 임시 세션 만료, SSO 또는 login 재인증 |
| `AccessDenied` | 현재 ARN, 필요한 작업·리소스 권한, 명시적 Deny·조직 정책 |
| `You must specify a region` | `--region` 또는 프로파일의 리전 |
| 자원이 보이지 않음 | 다른 계정·리전·필터로 조회했는지 |
| `Unknown options` | CLI 버전, 옵션 철자, 줄 연결·따옴표 |
| `Could not connect to the endpoint URL` | 리전·네트워크·프록시·엔드포인트 설정 |
| 인증서 검증 오류 | 시스템 시각·신뢰 CA·조직 프록시 설정 |

필요하면 `--debug`로 진단하되 출력에는 요청·환경 정보가 포함될 수 있어 공개하기 전에 내용을 확인합니다. 인증서 오류를 해결하려고 검증을 끄는 옵션을 기본 설정에 넣지는 않습니다.

## 시작 순서와 학습 기록

1. `aws --version`으로 v2 확인.
2. SSO 또는 지원되는 브라우저 로그인 중 자신의 환경에 맞는 한 가지 선택.
3. `aws sts get-caller-identity --profile study`로 계정·역할 확인.
4. `--region`을 지정해 EC2·S3 목록 등 조회부터 실행.
5. `--query`와 `--output`으로 필요한 결과만 정리.
6. 변경 명령은 대상·영향을 확인하고 학습용 자원에 실행.

이 요약본 작성 과정에서는 실제 AWS 계정 로그인·리소스 변경을 수행하지 않았습니다. 학습 기록에는 실행 목적·명령·예상 결과·오류 해결을 적고, 키·토큰과 민감한 실제 계정 정보는 빼세요.

[Terraform 사용법](terraform-reference.html) · [AWS 서비스 요약](aws-reference.html) · [GitHub 학습 기록 작성법](github-reference.html)
