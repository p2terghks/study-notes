# 프로젝트 4 · 서버리스 이벤트 이미지 처리

## 목표와 처리 흐름

**업로드 이벤트를 받아 썸네일을 만들고 메타데이터를 저장**합니다. 서버 VM은 직접 운영하지 않지만 권한·재시도·중복·비용·실패 알림은 여전히 설계해야 합니다.

```text
IAM 인증 클라이언트 → API Gateway → 업로드 API Lambda
                                      ↓ 제한된 presigned POST
클라이언트 → 입력 S3 (버전 관리, uploads/)
                    ↓ Object Created
               EventBridge 규칙
                    ↓
               이미지 처리 Lambda
                 ├─ 출력 S3 / thumbnails/
                 └─ DynamoDB 메타데이터
실패 이벤트 → SQS 실패 큐 / CloudWatch 경보
```

[전체 코드 ZIP](sample-files/cloud-projects.zip)의 `serverless/`와 `infra/serverless/`를 사용합니다. API는 서명 URL 발급, worker는 실제 이미지 처리로 역할을 나눕니다. 입력과 출력 버킷을 분리해 생성한 썸네일이 다시 worker를 호출하지 않게 합니다.

## 로컬에서 실제 썸네일 만들기

Python 3.12 이상을 사용하며 `cloud-projects` 폴더에서 실행합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r serverless/requirements.txt
PYTHONPATH=serverless python -m unittest discover -s serverless/tests -v
python serverless/local_demo.py
```

`serverless/build/local/`에 source.png, thumbnails 폴더, metadata.json이 생깁니다. 샘플 원본 1000×600을 320×192 JPEG로 만들고, 두 번째 동일 이벤트는 duplicate로 처리합니다. 이 실습은 실제 Pillow 변환을 실행하지만 AWS 서비스는 로컬 어댑터로 대체합니다. 실제 EventBridge 전달이나 IAM 검증은 아닙니다.

## 이벤트 구조와 핵심 코드

```json
{
  "source": "aws.s3",
  "detail-type": "Object Created",
  "detail": {
    "bucket": {"name": "INPUT_BUCKET"},
    "object": {"key": "uploads/demo.png", "version-id": "SOURCE_VERSION"}
  }
}
```

worker는 입력 버킷과 uploads/ 접두사를 확인하고, `VersionId`를 지정해 해당 업로드 버전만 읽습니다. S3의 일반 Notification 형식과 EventBridge의 detail 형식을 혼동하지 않습니다. 이 구현은 EventBridge에서 받은 key를 그대로 사용하므로 공백·더하기 기호를 임의로 다시 URL 디코딩하지 않습니다. [AWS 공식 EventBridge 메시지 구조](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html)

## 중복과 순서 뒤바뀜에 대응하기

**버킷·키·버전 ID의 해시를 image_id로 사용**합니다. 같은 이벤트는 같은 image_id, 서로 다른 업로드 버전은 다른 image_id를 갖습니다.

1. DynamoDB에 처리 결과가 이미 있으면 duplicate로 끝냅니다.
2. 입력 S3의 정확한 VersionId를 읽습니다.
3. 고정된 `thumbnails/{image_id}.jpg` 경로에 변환 결과를 씁니다.
4. `attribute_not_exists(image_id)` 조건으로 메타데이터를 기록합니다.

S3 저장 후 DynamoDB 기록에 실패하면 재시도에서 같은 출력 키에 다시 저장합니다. 두 worker가 동시에 처리해도 결과 경로가 같고 메타데이터 중복 삽입은 방지합니다. 계산 자체가 정확히 한 번 실행되는 보장은 아닙니다. 오래된 이벤트가 늦게 와도 별도 버전 결과로 남으므로 최신 썸네일을 덮어쓰지 않습니다. 이 예제에는 ‘항상 최신 버전 하나만 조회’하는 인덱스는 없습니다.

## 이미지와 업로드 제한

| 항목 | 구현 |
|---|---|
| 업로드 인증 | HTTP API AWS_IAM |
| URL 만료 | 300초 |
| 파일 크기 | 최대 5 MiB, presigned POST 정책과 worker 양쪽 검사 |
| 이미지 형식 | PNG/JPEG, 실제 이미지 디코딩으로 확인 |
| 픽셀 수 | Pillow의 2천만 픽셀 경고를 오류로 처리 |
| 출력 | 최대 320×320, 비율 유지, 작은 이미지는 확대하지 않음 |
| 메타데이터 | EXIF 방향 보정 후 JPEG 변환, 원본 메타데이터를 그대로 복사하지 않음 |

버킷은 공개하지 않습니다. presigned URL을 아는 사람은 만료 전 업로드할 수 있으므로 토큰처럼 다룹니다. 파일 확장자나 Content-Type만으로 이미지 안전성을 단정하지 않습니다. 허용 크기 안의 잘못된 이미지도 실패 큐에서 확인해야 합니다.

## Lambda 패키지 만들기

```bash
./scripts/package-lambda.sh
terraform -chdir=infra/serverless init -backend=false
terraform -chdir=infra/serverless validate
```

스크립트는 **Linux x86_64·Python 3.12**용 바이너리 휠을 받아 function.zip을 만듭니다. Mac에서 설치한 Pillow 라이브러리를 그대로 압축하면 Lambda에서 로드되지 않을 수 있습니다. 로컬 테스트 환경과 배포 타깃을 구분하세요. ZIP의 함수 진입점은 `worker.handler`, `api.handler`입니다.

`infra/serverless/main.tf.json`은 Terraform의 JSON 문법으로, HCL `.tf`와 같은 리소스 그래프를 구성합니다. 기본 구현은 S3·DynamoDB가 퍼블릭 AWS API를 사용하므로 Lambda를 VPC에 연결하지 않습니다.

## AWS에서 추가 확인할 순서 — 이번에는 미실행

1. IaC 가이드대로 state backend와 serverless 변수 파일을 준비합니다.
2. ZIP을 만든 뒤 plan/apply를 검토하여 적용합니다.
3. 호출자에게 출력 API의 `POST /uploads`에 한정한 `execute-api:Invoke` 권한을 부여합니다.
4. 인증된 클라이언트로 이미지를 업로드합니다.

```bash
python scripts/upload-image.py https://API_ID.execute-api.ap-northeast-2.amazonaws.com sample.png --region ap-northeast-2
```

위 스크립트는 AWS 자격증명이 필요한 **추후 클라우드 명령**입니다. 로컬 데모에서는 실행하지 않습니다.

5. EventBridge 규칙 일치, Lambda 로그, 출력 S3, DynamoDB 항목을 순서대로 확인합니다.
6. 같은 key의 다른 버전, 동일 이벤트 재전달, 잘못된 이미지, DynamoDB 오류를 시험합니다.
7. S3 버킷에 EventBridge 전송을 활성화했는지도 확인합니다. [S3 EventBridge 연동](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventBridge.html)

## 재시도·실패 큐·관측

EventBridge 전달 실패와 Lambda 비동기 실행 실패는 다른 단계입니다. 두 단계 모두 제한된 재시도와 SQS 실패 큐를 구성했으며, 큐 메시지에는 서로 다른 실패 형식이 들어올 수 있습니다. 자동 재처리는 구현하지 않았습니다. 원인을 수정한 뒤 원본 이벤트를 확인해 worker에 다시 전달하는 절차가 필요합니다.

Lambda Errors와 SQS 대기 메시지 경보를 만들지만 SNS/이메일 수신자는 지정하지 않았습니다. 운영 시 경보 action을 실제 알림 채널에 연결하세요. Lambda 동시 실행 수는 함수당 2로 제한했으며 신규 계정의 계정 동시성 할당량 조건에 따라 설정을 조정해야 할 수 있습니다.

Lambda 성공 수뿐 아니라 입력 수·출력 수·중복 수·실패 큐 개수·처리 시간을 함께 기록합니다. 출력 없는 이벤트가 모두 성공으로 집계되는지 반드시 점검하세요.

## 비용 기록과 정리

| 비용 항목 | 기록할 양 |
|---|---|
| API Gateway·Lambda | API 호출 수, worker 실행 수, 메모리×실행 시간 |
| S3 | 원본/버전/썸네일 저장량, PUT/GET 요청 |
| DynamoDB | 읽기·쓰기 요청, 저장량, PITR |
| EventBridge·SQS | 해당 이벤트 경로의 과금 조건, 큐 요청 |
| CloudWatch | 로그 유입·보관, 경보 개수 |

원본·썸네일은 실습용 7일 수명주기를 설정했습니다. 입력의 이전 버전도 7일 경과 후 정리 대상입니다. DynamoDB 메타데이터는 자동 삭제하지 않으므로 객체 만료 후 항목이 남을 수 있습니다. 장기 운영에는 일관된 보존·삭제 정책을 추가합니다.

사용 전후 Billing/Cost Explorer에서 Project 태그와 사용량을 비교하고, 태그 활성화·청구 데이터 지연도 기록합니다. ‘서버리스=항상 무료’가 아니라 **처리량과 보관량에 따른 비용**으로 설명하세요. [AWS 요금 계산기](https://calculator.aws/)

Terraform은 데이터가 남은 S3 버킷을 강제 삭제하지 않습니다. 실습 종료 시 저장할 자료를 백업하고 버전/삭제 마커/실패 큐/로그를 확인한 뒤 정리합니다.
