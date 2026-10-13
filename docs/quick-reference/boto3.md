## Boto3란 무엇인가

**Boto3는 Python 코드로 AWS API를 호출하는 SDK입니다.** 콘솔에서 버튼으로 하던 파일 업로드·서버 조회·메시지 전송을 함수 호출로 자동화할 수 있습니다. Botocore는 요청 서명, 통신, 서비스 모델, 재시도 등 기반 기능을 담당합니다.

|도구|용도|예|
|---|---|---|
|AWS 콘솔|사람이 화면에서 작업|S3 객체 보기|
|AWS CLI|터미널 명령|`aws s3 ls`|
|Boto3|Python 프로그램 안의 AWS 작업|앱의 파일 업로드·운영 점검|
|Terraform|원하는 인프라 상태를 선언·관리|버킷·VPC·IAM 구성|

Boto3는 Terraform처럼 state를 보관하여 인프라 전체를 조정하는 도구가 아닙니다. 각 API의 결과를 받아 프로그램이 다음 행동을 결정합니다. Terraform 관리 자원의 설정을 Boto3로 바꾸면 drift가 생길 수 있으므로 책임을 나눕니다.

이 가이드는 읽기·쓰기·상태 변경 예제를 구분합니다. 짧은 발췌는 앞에서 만든 session/client와 실제 리소스가 필요합니다. 마지막 ZIP은 AWS 계정 없이 테스트할 수 있는 S3 목록 실습입니다. [공식 시작 안내](https://docs.aws.amazon.com/boto3/latest/guide/quickstart.html).

## 설치와 가상환경

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install boto3
python -c 'import boto3; print(boto3.__version__)'
```

Windows PowerShell에서는 가상환경 활성화 경로가 `.venv\Scripts\Activate.ps1`입니다. 설치한 Python과 실행하는 Python이 다르면 ModuleNotFoundError가 발생합니다. `python -m pip`를 사용하면 현재 인터프리터에 설치하기 쉽습니다.

```bash
# 검증된 환경의 의존성 기록
python -m pip freeze > requirements-lock.txt
# 다른 환경에서 재현
python -m pip install -r requirements-lock.txt
```

Boto3와 Botocore는 호환되는 조합을 사용합니다. 임의로 한쪽만 고정하여 의존성 충돌을 만들지 않습니다. SDK가 최신 AWS API를 모른다는 오류가 나면 문서와 설치 버전을 함께 확인합니다. 이 문서의 코드 문법은 Python 3.10 이상을 대상으로 하며 설치 버전의 Python 지원 조건도 확인하세요.

## 인증: 키를 코드에 넣지 않기

로컬에서는 AWS CLI로 IAM Identity Center(SSO) 프로파일을 구성한 뒤 사용하면 편리합니다.

```bash
aws configure sso --profile study
aws sso login --profile study
aws sts get-caller-identity --profile study
```

```python
import boto3
session = boto3.Session(profile_name="study", region_name="ap-northeast-2")
sts = session.client("sts")
identity = sts.get_caller_identity()
print(identity["Account"], identity["Arn"])
```

Account는 현재 AWS 계정, Arn은 호출 주체입니다. 쓰기 작업 전에는 예상 계정인지 확인합니다. 인증 성공과 S3 읽기 권한은 별개입니다.

|실행 위치|권장 자격증명 출처|
|---|---|
|개발자 PC|SSO 프로파일·임시 자격증명|
|EC2|인스턴스 역할|
|ECS|Task role|
|Lambda|실행 역할|
|GitHub Actions|OIDC로 받은 역할의 임시 자격증명|

Boto3는 명시적 자격증명, 환경변수, 프로파일, 역할 자격증명 등의 탐색 체인을 사용합니다. 남아 있는 환경변수가 의도와 다른 인증에 영향을 줄 수 있습니다. 전체 env나 token을 출력하지 말고 STS로 주체를 확인합니다. AWS 환경에서는 보통 `boto3.Session(region_name=...)`처럼 프로파일명을 강제하지 않습니다. [자격증명 공식 안내](https://docs.aws.amazon.com/boto3/latest/guide/credentials.html).

## Session · client · resource 차이

```python
session = boto3.Session(region_name="ap-northeast-2")
s3 = session.client("s3")
dynamodb = session.resource("dynamodb")
table = dynamodb.Table("study-todos")
```

|객체|역할|예|
|---|---|---|
|Session|리전·인증·프로파일의 출발점|`session.client("s3")`|
|client|AWS API와 가까운 메서드 제공|`s3.list_objects_v2(...)`|
|resource|일부 서비스를 객체처럼 다루는 추상화|`table.get_item(...)`|
|response|대개 dict 형태의 응답|`response.get("Contents", [])`|

resource를 만든 것만으로 실제 테이블·버킷을 생성하지는 않습니다. 일부 속성 접근은 지연 API 호출을 발생시킬 수 있습니다. 새 기능은 client에 먼저 제공될 수 있으며 Boto3 resource 인터페이스에는 새로운 기능 추가 계획이 없다는 공식 안내가 있습니다. 신규 API는 client 문서를 기준으로 확인하세요. [Resources](https://docs.aws.amazon.com/boto3/latest/guide/resources.html).

## 공통 설정: timeout과 재시도

```python
from botocore.config import Config

config = Config(
    connect_timeout=5,
    read_timeout=30,
    retries={"mode": "standard", "total_max_attempts": 4},
)
s3 = session.client("s3", config=config)
```

|설정|의미|주의|
|---|---|---|
|connect_timeout|연결 대기 제한|작업 전체 제한 시간이 아님|
|read_timeout|응답 읽기 대기 제한|SQS long polling보다 충분히 길게|
|mode=standard|표준 재시도 정책|모든 오류가 재시도 대상은 아님|
|total_max_attempts=4|첫 시도 포함 최대 4회|재시도 횟수만 4회가 아님|
|max_pool_connections|연결 풀 크기|스레드 수 자체를 제한하는 옵션 아님|

SDK 재시도와 사용자 코드의 반복 재시도를 겹치면 호출 수와 대기 시간이 늘어납니다. AccessDenied나 잘못된 인수는 반복 호출로 해결되지 않습니다. [재시도 문서](https://docs.aws.amazon.com/boto3/latest/guide/retries.html).

## 메서드·인수·응답 읽는 법

```python
response = s3.list_objects_v2(
    Bucket="YOUR_BUCKET",
    Prefix="reports/",
    MaxKeys=10,
)
for item in response.get("Contents", []):
    print(item["Key"], item["Size"])
```

메서드는 보통 snake_case지만 AWS 요청 인수는 `Bucket`, `Prefix`처럼 대문자로 시작합니다. `bucket=`으로 바꾸면 같은 인수가 아닙니다. 문서의 Request Syntax, 필수 항목, Response Structure를 함께 보세요.

|문법|역할|
|---|---|
|`Bucket=`|이미 있는 버킷 이름|
|`Prefix=`|객체 key의 시작 문자열|
|`response.get("Contents", [])`|빈 결과에서 누락될 수 있는 키 처리|
|`item["Key"]`|객체 key|
|`ResponseMetadata`|HTTP 상태·요청 ID 등 진단 정보|

한 번의 list 호출이 전체 목록을 뜻하지 않습니다. 위 코드는 **첫 페이지 최대 10개를 조회하는 예**입니다. 모든 항목은 다음 장의 paginator로 읽습니다. SDK 응답에는 datetime, Decimal, StreamingBody 등이 포함될 수 있어 `json.dumps(response)`가 항상 성공하지는 않습니다.

## 페이지네이션: 전체 결과 누락 막기

```python
def iter_objects(s3_client, bucket, prefix=""):
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        yield from page.get("Contents", [])

for obj in iter_objects(s3, "YOUR_BUCKET", "reports/"):
    print(obj["Key"], obj["Size"])
```

get_paginator는 해당 API의 페이지 이동 규칙을 제공하고 paginate는 여러 페이지를 순회합니다. yield from은 각 페이지의 객체를 하나씩 내보내므로 전체 목록을 메모리에 모을 필요가 없습니다.

|PaginationConfig|역할|
|---|---|
|PageSize|요청 페이지 크기 힌트, 서비스별 지원 확인|
|MaxItems|paginator가 돌려줄 총 항목 제한|
|StartingToken|이전 탐색을 이어가는 SDK 토큰|

MaxItems를 넣고 전체 조회라고 설명하면 안 됩니다. SDK StartingToken과 서비스 ContinuationToken은 구분합니다. 모든 API가 paginator를 제공하지는 않으며 `can_paginate()`로 확인할 수 있습니다. [Paginators](https://docs.aws.amazon.com/boto3/latest/guide/paginators.html).

## S3 파일 업로드·다운로드

**업로드는 AWS 쓰기, 다운로드는 로컬 파일 쓰기입니다.** 버킷과 디렉터리가 준비되어 있어야 합니다.

```python
from pathlib import Path

s3.upload_file(
    Filename="report.csv",
    Bucket="YOUR_BUCKET",
    Key="reports/report.csv",
    ExtraArgs={"ContentType": "text/csv"},
)
Path("downloads").mkdir(exist_ok=True)
s3.download_file("YOUR_BUCKET", "reports/report.csv", "downloads/report.csv")
```

upload_file/download_file은 파일 전송용 고수준 메서드로 큰 파일의 multipart 전송 등을 관리합니다. 성공 시 일반 API처럼 응답 dict를 반환한다고 가정하지 않습니다. 같은 Key 업로드는 기존 객체를 대체하거나 버전 관리가 켜져 있으면 새 버전을 만듭니다.

Key의 `/`는 일반 목적 S3에서 파일 시스템 디렉터리가 아닌 이름의 일부입니다. 다운로드할 로컬 파일명에 신뢰하지 않는 key를 그대로 붙이면 경로 이탈 문제가 생길 수 있으므로 목적 경로를 검증합니다. [업로드](https://docs.aws.amazon.com/boto3/latest/guide/s3-uploading-files.html), [다운로드](https://docs.aws.amazon.com/boto3/latest/guide/s3-example-download-file.html).

## S3 작은 데이터·스트리밍·메타데이터

```python
import json
payload = json.dumps({"status": "ok"}, ensure_ascii=False).encode("utf-8")
s3.put_object(Bucket="YOUR_BUCKET", Key="status.json",
              Body=payload, ContentType="application/json")

response = s3.get_object(Bucket="YOUR_BUCKET", Key="status.json")
body = response["Body"]
try:
    document = json.loads(body.read().decode("utf-8"))
finally:
    body.close()
```

put_object는 메모리에 있는 bytes/파일형 객체를 저장할 때 사용합니다. get_object의 Body는 이미 완성된 문자열이 아니라 StreamingBody입니다. 위 read는 **작은 파일용**으로 전체를 메모리에 읽습니다. 큰 파일은 download_file 또는 iter_chunks로 나눠 처리합니다.

`head_object(Bucket=..., Key=...)`는 본문 없이 ContentLength, ContentType 등 메타데이터를 확인합니다. 403이 나왔다고 객체가 없다고 단정할 수 없으며 호출자의 목록 권한 등도 결과에 영향을 줍니다.

객체 삭제는 `delete_object`이며 복구 조건은 버전 관리와 VersionId 지정 여부에 따라 다릅니다. 목록 학습 코드에 자동 삭제를 섞지 않습니다.

## Presigned URL: 임시 파일 접근 링크

```python
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": "YOUR_BUCKET", "Key": "reports/report.csv"},
    ExpiresIn=300,
)
```

이 함수는 서명된 URL을 만들며 직접 파일을 다운로드하지 않습니다. URL을 가진 사람이 유효 기간 동안 해당 요청을 보낼 수 있으므로 로그·공개 채팅에 남기지 않습니다. 서명한 주체의 권한과 자격증명 유효 기간, 버킷 정책이 적용되며 임시 자격증명이 먼저 만료되면 URL도 더 일찍 사용할 수 없게 됩니다.

업로드용 put_object URL이나 presigned POST를 사용할 수도 있습니다. 클라이언트가 지정할 수 있는 key·크기·ContentType 범위를 서버가 통제해야 합니다. 브라우저 호출이면 S3 CORS도 별도입니다. [Presigned URL](https://docs.aws.amazon.com/boto3/latest/guide/s3-presigned-urls.html).

## EC2 조회: 리전·필터·중첩 응답

```python
ec2 = session.client("ec2", config=config)
pages = ec2.get_paginator("describe_instances").paginate(
    Filters=[
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag:Environment", "Values": ["dev"]},
    ]
)
for page in pages:
    for reservation in page.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            print(instance["InstanceId"], instance["State"]["Name"])
```

Instances가 응답 최상위에 바로 있는 것이 아니라 Reservations 안에 들어 있습니다. 리전이 다르면 기대한 인스턴스가 안 보일 수 있습니다. 여러 Filters 조건과 Values 조합의 의미는 API 문서를 확인합니다.

태그에서 Name을 꺼낼 때는 태그가 없을 수도 있습니다.

```python
tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
name = tags.get("Name", "(이름 없음)")
```

[EC2 describe_instances](https://docs.aws.amazon.com/boto3/latest/reference/services/ec2/client/describe_instances.html).

## EC2 상태 변경과 waiter

아래는 **실제 인스턴스를 중지하는 코드**입니다. 본인 개발 인스턴스 ID로 대상을 확정한 경우에만 사용합니다.

```python
instance_ids = ["i-REPLACE_WITH_DEV_INSTANCE"]
# ec2.stop_instances(InstanceIds=instance_ids)  # 상태 변경 시 명시적으로 실행
waiter = ec2.get_waiter("instance_stopped")
# 중지 요청 후에만 대기
# waiter.wait(InstanceIds=instance_ids,
#             WaiterConfig={"Delay": 10, "MaxAttempts": 30})
```

API가 요청을 수락했다고 목표 상태에 도달한 것은 아닙니다. waiter는 주기적으로 상태를 조회합니다. `WaiterError`는 대기 실패·한도 초과 등을 나타내므로 현재 상태를 다시 조사합니다. running waiter가 통과해도 웹 앱 준비 완료는 별도입니다.

|메서드|기능|주의|
|---|---|---|
|start_instances|시작|컴퓨팅 비용 재개 가능|
|stop_instances|중지|EBS 등 비용까지 모두 사라지는 것은 아님|
|reboot_instances|재부팅|진행 중 요청 영향|
|terminate_instances|종료·삭제|복구와 데이터 보존 조건 확인|

DryRun은 지원하는 API에서 권한 확인 등에 유용하지만 Terraform plan처럼 모든 변경·비용을 예측하지 않습니다. 권한이 있으면 DryRunOperation 오류를 돌려주는 방식도 있어 정상 응답과 구분해야 합니다.

## DynamoDB: client와 resource의 데이터 표현

```python
from decimal import Decimal
dynamodb = session.resource("dynamodb")
table = dynamodb.Table("study-todos")

# 쓰기: pk가 파티션 키인 기존 테이블을 전제로 함
table.put_item(
    Item={"pk": "TODO#1", "title": "Boto3 공부", "cost": Decimal("0.1")},
    ConditionExpression="attribute_not_exists(pk)",
)
response = table.get_item(Key={"pk": "TODO#1"}, ConsistentRead=True)
item = response.get("Item")
```

resource는 Python dict와 Decimal을 사용합니다. 저수준 client는 `{"pk": {"S": "TODO#1"}}`처럼 DynamoDB 타입 표기를 사용합니다. 두 형식을 섞지 않습니다. float는 Decimal로 명시적으로 변환하고 `Decimal(0.1)`보다 문자열 기반 `Decimal("0.1")`로 의도를 보존합니다.

get_item에 없는 항목은 Item이 누락될 수 있습니다. sort key가 있는 테이블은 Key에 그것도 포함해야 합니다. put_item은 같은 키를 덮어쓸 수 있으므로 예제처럼 조건식을 쓰면 기존 항목을 보호할 수 있습니다. [DynamoDB 가이드](https://docs.aws.amazon.com/boto3/latest/guide/dynamodb.html).

## DynamoDB Query · Scan · Update

```python
from boto3.dynamodb.conditions import Key

# pk 파티션 키와 sk 정렬 키가 있는 테이블 예제
args = {"KeyConditionExpression": Key("pk").eq("USER#1") & Key("sk").begins_with("TODO#")}
while True:
    response = table.query(**args)
    for item in response.get("Items", []):
        print(item["sk"])
    token = response.get("LastEvaluatedKey")
    if not token:
        break
    args["ExclusiveStartKey"] = token
```

Query는 키 조건으로 탐색하고 Scan은 테이블/인덱스 전반을 읽습니다. FilterExpression은 읽은 뒤 필터링하므로 읽기 비용을 줄이는 키 조건의 대체재가 아닙니다. Items가 비어 있어도 LastEvaluatedKey가 있으면 계속 조회해야 합니다. GSI에서는 강한 일관성 읽기를 지원하지 않습니다.

```python
# pk만 사용하는 앞 장의 테이블 기준: 실제 쓰기
response = table.update_item(
    Key={"pk": "TODO#1"},
    UpdateExpression="SET #t = :title",
    ExpressionAttributeNames={"#t": "title"},
    ExpressionAttributeValues={":title": "복습 완료"},
    ConditionExpression="attribute_exists(pk)",
    ReturnValues="ALL_NEW",
)
```

속성 이름 placeholder는 예약어 충돌을 피하고 값 placeholder는 값을 표현식 문자열과 분리합니다. 조건 없이 update하면 없는 항목이 만들어질 수 있습니다. batch 작업의 일부 실패·미처리 항목도 확인해야 하며 batch_writer가 트랜잭션을 보장하지는 않습니다.

## SQS: 전송 → 처리 → 성공 후 삭제

```python
import json
sqs = session.client("sqs", config=config)
queue_url = "YOUR_QUEUE_URL"
# 전송은 실제 쓰기
sqs.send_message(QueueUrl=queue_url,
                 MessageBody=json.dumps({"todo_id": "1"}))

response = sqs.receive_message(
    QueueUrl=queue_url, MaxNumberOfMessages=10,
    WaitTimeSeconds=20, VisibilityTimeout=60,
)
for message in response.get("Messages", []):
    payload = json.loads(message["Body"])
    # process_idempotently(payload)  # 실제 업무 처리 함수를 구현
    # 처리 성공 후에만 아래 삭제를 실행
    # sqs.delete_message(QueueUrl=queue_url,
    #                    ReceiptHandle=message["ReceiptHandle"])
```

수신은 단순 읽기만이 아니라 visibility timeout 동안 다른 소비자에게 메시지를 숨기는 동작입니다. 삭제에는 MessageId가 아니라 **현재 수신의 ReceiptHandle**을 사용합니다. 처리 실패 시 삭제하지 않고 재처리·DLQ 정책으로 넘깁니다.

Standard 큐는 중복 수신을 전제로 업무 멱등성을 설계합니다. 작업 시간이 길면 change_message_visibility로 연장합니다. FIFO는 MessageGroupId와 중복 제거 설정 등이 추가로 필요합니다. [receive_message](https://docs.aws.amazon.com/boto3/latest/reference/services/sqs/client/receive_message.html).

## Lambda 호출과 함수 오류 확인

```python
import json
lambda_client = session.client("lambda", config=config)
response = lambda_client.invoke(
    FunctionName="YOUR_FUNCTION_NAME",
    InvocationType="RequestResponse",
    Payload=json.dumps({"todo_id": "1"}).encode("utf-8"),
)
stream = response["Payload"]
try:
    result = json.loads(stream.read())
finally:
    stream.close()
if response.get("FunctionError"):
    raise RuntimeError("Lambda 실행 실패: 별도 로그 확인")
```

호출 API의 HTTP 성공과 Lambda 내부 업무 성공은 다릅니다. 동기 호출은 FunctionError와 반환 데이터의 계약을 함께 봅니다. InvocationType=Event는 비동기 접수로, 응답을 받았다고 업무 완료를 뜻하지 않습니다. 재시도·중복 이벤트·실패 목적지를 설계합니다. 위 코드는 JSON 반환을 가정한 예이며 호출 자체가 업무 부작용을 만들 수 있습니다. [invoke](https://docs.aws.amazon.com/boto3/latest/reference/services/lambda/client/invoke.html).

## Secrets Manager · Parameter Store

```python
import json
secrets = session.client("secretsmanager", config=config)
response = secrets.get_secret_value(SecretId="YOUR_SECRET_ID")
# SecretString에 JSON이 저장된 경우
credentials = json.loads(response["SecretString"])
# credentials 전체를 print/log 하지 않음

ssm = session.client("ssm", config=config)
value = ssm.get_parameter(Name="/study/api/url", WithDecryption=True)["Parameter"]["Value"]
```

secret이 일반 문자열인지 JSON인지, SecretBinary인지에 따라 처리해야 합니다. 앱에서 매 요청마다 조회하면 지연·호출 비용이 늘 수 있으므로 만료·회전 정책에 맞게 캐시합니다. 무기한 캐시는 회전된 비밀을 못 읽게 만듭니다.

필요한 secret/parameter ARN에만 권한을 주고 고객 관리 KMS 키를 쓰면 키 복호화 권한·정책도 확인합니다. 코드에 없는 비밀이라도 로그·오류 응답·덤프에 남으면 노출될 수 있습니다. [Secret 조회](https://docs.aws.amazon.com/boto3/latest/reference/services/secretsmanager/client/get_secret_value.html).

## 예외 처리: 오류 코드를 기준으로 분기

```python
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

try:
    response = s3.head_object(Bucket="YOUR_BUCKET", Key="reports/report.csv")
except NoCredentialsError:
    raise RuntimeError("AWS 인증 설정을 확인하세요")
except EndpointConnectionError:
    raise RuntimeError("리전·네트워크·endpoint를 확인하세요")
except ClientError as exc:
    code = exc.response["Error"]["Code"]
    request_id = exc.response.get("ResponseMetadata", {}).get("RequestId")
    print("AWS 요청 실패", code, request_id)
    raise
```

오류 메시지 전체 문자열은 바뀔 수 있으므로 Error.Code를 기준으로 처리합니다. 오류를 잡고 빈 목록을 반환하면 권한 실패를 “자료 없음”으로 숨길 수 있습니다. 파일 전송 헬퍼는 S3UploadFailedError 같은 별도 예외로 감쌀 수 있으므로 사용하는 메서드의 예외도 확인합니다.

|오류|우선 확인|
|---|---|
|NoCredentialsError|프로파일·역할·SSO 로그인|
|ExpiredToken|세션 갱신|
|AccessDenied|IAM·리소스 정책·SCP·KMS|
|NoRegionError|Session/환경의 리전|
|ParamValidationError|인수명·타입·필수값|
|Throttling 계열|호출량·재시도·동시성|
|WaiterError|현재 실제 상태·대기 한도|

[오류 처리](https://docs.aws.amazon.com/boto3/latest/guide/error-handling.html).

## IAM과 API 이름 연결하기

|Boto3 작업|대표 IAM action|범위|
|---|---|---|
|list_objects_v2|s3:ListBucket|버킷 ARN|
|get_object|s3:GetObject|객체 ARN `bucket/prefix/*`|
|put_object/upload_file|s3:PutObject|객체 ARN, multipart·KMS 등 추가 조건 확인|
|describe_instances|ec2:DescribeInstances|보통 Resource `*`|
|table.get_item|dynamodb:GetItem|테이블 ARN|
|table.query|dynamodb:Query|테이블/인덱스 ARN|
|send_message|sqs:SendMessage|큐 ARN|
|lambda.invoke|lambda:InvokeFunction|함수/alias ARN|

메서드명과 IAM action 이름이 항상 같지는 않습니다. 버킷 ARN과 객체 ARN을 혼동하면 AccessDenied가 납니다. IAM Allow가 있어도 명시적 Deny, SCP, permission boundary, 리소스 정책 등 때문에 거부될 수 있습니다. SDK가 최소 권한을 자동으로 만들어 주지는 않습니다.

## 동시성 · Lambda 재사용 · 멱등성

client는 일반적으로 스레드 간 공유가 가능하지만 metadata 변경·사용자 event hook 등 주의사항이 있습니다. Session/resource는 스레드 공유를 피하고 작업별로 만듭니다. client를 프로세스 간 공유하지 않습니다. 기본 boto3는 동기 SDK라 async def 안에서 직접 호출하면 이벤트 루프를 막을 수 있습니다.

Lambda에서는 모듈 전역에 client를 만들어 warm invocation 간 재사용할 수 있습니다. 요청 사용자 데이터·비밀 결과를 전역 mutable 상태로 쌓지 않습니다.

```python
import boto3
s3 = boto3.client("s3")

def handler(event, context):
    # 입력 bucket/key에 대해 업무상 접근 허용 범위를 먼저 검증
    return {"ok": True}
```

멱등성은 같은 업무 요청을 여러 번 받아도 중복 결제·중복 생성 등 잘못된 결과가 생기지 않게 하는 설계입니다. 지원 API의 ClientToken, DynamoDB 조건부 쓰기, 업무 요청 ID 기록 등을 활용합니다. “재시도 있음”과 “중복이 안전함”은 별개입니다. [Client 주의사항](https://docs.aws.amazon.com/boto3/latest/guide/clients.html).

## Stubber로 AWS 없이 테스트하기

```python
import boto3
from botocore.stub import Stubber

client = boto3.client(
    "s3", region_name="ap-northeast-2",
    aws_access_key_id="testing", aws_secret_access_key="testing",
)
with Stubber(client) as stub:
    stub.add_response(
        "list_objects_v2", {"IsTruncated": False},
        {"Bucket": "test-bucket", "Prefix": ""},
    )
    assert list(iter_objects(client, "test-bucket")) == []
    stub.assert_no_pending_responses()
```

testing은 **가짜 테스트 값**이며 실제 자격증명이 아닙니다. Stubber가 API 호출을 가로채 예상 응답을 돌려주므로 AWS 네트워크 요청을 하지 않습니다. add_response는 호출 순서·인수와 응답 모델을 검사하고 add_client_error는 AWS 오류를 재현합니다.

Stubber 테스트가 통과해도 IAM·실제 네트워크·서비스 quota 검증이 끝난 것은 아닙니다. 격리된 개발 환경의 통합 테스트는 별도입니다. [Stubber](https://docs.aws.amazon.com/botocore/latest/reference/stubber.html).

## 전체 실습: S3 목록을 JSON으로 출력

[실습 코드와 테스트 ZIP 다운로드](sample-files/boto3-lab.zip)

`inventory.py`는 S3 목록을 paginator로 읽고 Key/Size만 JSON으로 출력합니다. 기본 실행은 도움말만 표시하고 실제 조회에는 버킷·리전·예상 계정을 명시합니다. 쓰기·삭제 API는 사용하지 않습니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
# 이 명령은 실제 AWS 조회: 자신의 값으로 교체
python inventory.py --bucket YOUR_BUCKET --profile study \
  --region ap-northeast-2 --expected-account YOUR_12_DIGIT_ACCOUNT_ID \
  --prefix reports/
```

|파일|역할|
|---|---|
|inventory.py|페이지 순회·합계·계정 확인·CLI|
|test_inventory.py|빈 목록·다음 페이지·AccessDenied 검증|
|requirements.txt|검증한 SDK 버전|
|README.md|실행 순서와 기대 결과|

학습 순서: 빈 목록 테스트 → 여러 페이지 테스트 → Prefix 변경 → 출력 구조 변경 → 오류 전달 확인. 테스트에서 실제 AWS 키를 쓰지 않습니다.

공식 문서 확인일: **2026-10-13**. 테스트 결과는 ZIP의 VERIFICATION.md에 기록합니다. 이 가이드 작성에서는 실제 AWS 조회·업로드·중지·삭제를 수행하지 않았습니다.

[Python 심화](python-advanced-reference.html) · [AWS CLI](aws-cli-reference.html) · [Terraform](terraform-reference.html) · [CI/CD 실무](devops-handbook-reference.html)
