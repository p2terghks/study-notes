"""Generate a reproducible daily set using five independently checkable AWS rules."""
import datetime as dt
import json
import random
from pathlib import Path

root = Path(__file__).resolve().parents[2] / 'saa-daily'
date = dt.datetime.now(dt.timezone.utc).date()
rng = random.Random(date.isoformat())
items = []

def add(domain, stem, choices, tip, doc):
    options = [(str(label), why, i == 0) for i, (label, why) in enumerate(choices)]
    assert len(set(a for a, _, _ in options)) == 4
    rng.shuffle(options)
    items.append(dict(domain=domain, stem=stem, options=options, tip=tip, doc='https://docs.aws.amazon.com/'+doc))

n = rng.randint(16, 27)
total = 2**(32-n)
add('네트워크', f'운영팀이 일반 AWS IPv4 주소로 /{n} VPC 서브넷을 만들었다. 다른 리소스가 주소를 쓰지 않고 인스턴스당 주소 하나를 사용한다. 이 서브넷에 할당 가능한 인스턴스 주소는 최대 몇 개인가?', [
(total-5,f'전체 {total}개에서 AWS가 예약한 처음 네 주소와 마지막 한 주소를 제외한다.'),
(total,'CIDR 전체 주소 수다. 예약 주소까지 포함했다.'),(total-2,'일반적인 네트워크·브로드캐스트 주소만 뺐다. AWS의 추가 예약 주소가 빠졌다.'),(total-4,'처음 네 주소를 제외했지만 마지막 주소도 예약된다.')],
'일반 AWS IPv4 서브넷의 사용 가능 주소 = 2^(32 − 접두사 길이) − 5.', 'vpc/latest/userguide/subnet-sizing.html')

r = rng.randint(31,91)*10
duration = rng.choice([2,3,4])
add('서버리스', f'결제 함수가 정상 상태에서 초당 {r}건을 균일하게 처리한다. 한 실행은 평균 {duration}초 동안 요청 하나를 처리한다. 여유 용량을 제외한 평균 동시 실행 수는?', [
(r*duration,f'초당 도착량에 실행 시간을 곱한다. {r} × {duration}개의 실행 환경이 평균적으로 사용 중이다.'),
(r,'초당 요청 수다. 이전 초에 시작한 요청도 실행 중이다.'),(round(r/duration),'실행 시간이 길어지면 처리 중인 요청은 늘어난다. 나눗셈은 반대로 계산한다.'),(r*duration*2,'두 배의 여유 용량은 문제에서 요구한 평균 사용량에 포함되지 않는다.')],
'Lambda 평균 동시성 = 초당 요청 수 × 평균 실행 시간(초).','lambda/latest/dg/lambda-concurrency.html')

kb=rng.randint(3,15)*4-1
rate=rng.randint(15,84)*2
units=(kb+3)//4*rate
add('데이터베이스', f'DynamoDB 테이블에서 초당 {rate}번 GetItem을 수행한다. 항목은 각각 {kb} KiB이고 최신 쓰기를 즉시 반영해야 한다. 트랜잭션과 캐시는 사용하지 않는다. 필요한 최소 읽기 용량은 몇 RCU인가?', [
(units,f'각 항목을 4 KiB 단위로 올림하면 {(kb+3)//4}단위다. 강한 일관성 읽기이므로 요청 수 {rate}를 곱한다.'),(units//2,'최종 일관성 읽기의 소비량이다. 최신 쓰기 반영 조건을 충족하지 못한다.'),(units*2,'트랜잭션 읽기에 적용하는 두 배의 비용을 포함했다.'),(rate,'항목이 4 KiB 이하일 때의 값이다. 이 항목은 여러 읽기 단위를 사용한다.')],
'강한 일관성 GetItem은 항목별로 4 KiB 단위 올림 후 요청 수를 곱한다.','amazondynamodb/latest/developerguide/read-write-operations.html')

size=rng.randint(12,95)
part=rng.choice([16,32,64,128])
count=size*1024//part
add('스토리지',f'영상 서비스가 {size} GiB 파일을 S3에 멀티파트 업로드한다. 각 파트는 {part} MiB이며 재전송은 없다. 시작·완료 요청을 제외하고 UploadPart를 몇 번 보내는가?',[
(count,f'{size} GiB를 MiB로 바꾼 뒤 {part}로 나누면 {count}개다. 각 파트에 UploadPart가 한 번 필요하다.'),(count+2,'업로드 시작과 완료는 별도 API 호출이다. UploadPart 횟수에 포함하지 않는다.'),(count+1,'파일이 파트 크기로 나누어떨어진다. 빈 마지막 파트를 덧붙일 필요가 없다.'),(count*2,'각 파트는 한 번만 전송한다. 같은 파트를 두 번 보낼 필요가 없다.')],
'파트 수 = 올림(객체 크기 ÷ 파트 크기). 시작·완료 요청은 별도로 센다.','AmazonS3/latest/userguide/mpuoverview.html')

cap=rng.randint(12,65)
zones=rng.choice([2,3,4])
per=(cap+zones-2)//(zones-1)
add('고가용성',f'웹 서버 한 대는 피크 부하의 1/{cap}을 처리한다. {zones}개 AZ에 동일 수의 서버를 배치한다. AZ 하나가 중단되어도 증설 없이 피크를 처리하려면 각 AZ에 최소 몇 대가 필요한가?',[
(per,f'장애 후 {zones-1}개 AZ가 남는다. 이들이 총 {cap}대 이상의 처리량을 제공하도록 나눠 올림한다.'),(per-1,f'장애 후 총 {(per-1)*(zones-1)}대만 남아 피크 부하에 부족하다.'),(per+1,'부하는 감당하지만 각 AZ에 한 대씩 더 배치하므로 최소 구성 조건을 벗어난다.'),(per*zones,'전체 배치 대수를 AZ별 수량으로 계산했다.')],
'균등 분산 시 AZ당 최소 용량 = 올림(피크 필요 대수 ÷ 장애 후 남는 AZ 수).','wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html')

# Alternate capacity questions with design decisions. Distractors describe real
# services and explain the missing requirement in this scenario.
design = [
('보안','외부 회계 업체가 여러 고객의 AWS 계정을 점검한다. 장기 키를 전달하지 않고 고객 A의 요청으로 고객 B의 역할을 사용하는 혼동도 방지해야 한다. 어떤 구성이 적합한가?',[
('교차 계정 역할과 고객별 ExternalId','업체 역할을 신뢰하고 고객마다 다른 ExternalId 조건을 검사하면 잘못된 고객을 대신한 역할 수임을 방지한다.'),
('업체에 IAM 사용자 키 발급','장기 키를 외부에 배포하게 되며 고객 요청과 역할 간의 연결도 검증하지 않는다.'),
('Organizations SCP만 적용','SCP는 멤버 계정의 최대 권한을 제한한다. 외부 업체에 임시 세션을 발급하는 신뢰 관계가 추가로 필요하다.'),
('버킷의 기본 암호화 사용','저장 데이터의 암호화는 역할을 누가 어떤 고객을 대신해 수임했는지 판별하지 않는다.')],
'외부 업체의 역할 수임은 신뢰 정책, 고객별 ExternalId, 최소 권한을 함께 설계한다.','IAM/latest/UserGuide/id_roles_common-scenarios_third-party.html'),
('네트워크','프라이빗 서브넷의 배치 작업이 같은 리전의 S3에 대량 업로드한다. 인터넷 경로 없이 S3에 접근하고 NAT 데이터 처리 비용도 줄이려면?',[
('S3 게이트웨이 엔드포인트를 서브넷 라우팅 테이블에 연결','S3 접두사 목록에 해당하는 트래픽이 엔드포인트를 사용한다. 해당 트래픽에 NAT 처리가 필요하지 않다.'),
('NAT 게이트웨이의 수를 늘린다','AZ별 장애 격리는 개선할 수 있지만 S3 트래픽이 계속 NAT를 통과해 처리 비용이 발생한다.'),
('S3 Transfer Acceleration을 활성화한다','원거리 업로드를 가속하는 기능이다. VPC 내부에서 S3로 향하는 사설 경로를 만들지 않는다.'),
('버킷에 VPC 엔드포인트 조건만 추가한다','정책 조건은 요청을 제한한다. 엔드포인트와 경로를 먼저 구성해야 네트워크 연결이 가능하다.')],
'같은 리전 S3 접근은 게이트웨이 엔드포인트와 서브넷의 라우팅 테이블 연결을 확인한다.','vpc/latest/privatelink/vpc-endpoints-s3.html'),
('데이터 복구','운영자가 RDS for PostgreSQL 주문 행을 실수로 삭제했다. 자동 백업 보존 기간 안이며 삭제 직전 시각을 알고 있다. 현재 인스턴스의 후속 주문도 보존하려면?',[
('별도 인스턴스로 시점 복구 후 필요한 행을 대조·복사한다','삭제 직전 데이터를 새 인스턴스에서 읽어 현재 운영 데이터와 키 충돌을 확인하고 선별 복구할 수 있다.'),
('Multi-AZ 장애 조치를 수행한다','대기 인스턴스에도 삭제가 복제된다. 장애 조치는 정상 데이터베이스의 이전 상태를 제공하지 않는다.'),
('지금 읽기 전용 복제본을 생성한다','삭제 후 원본을 복제하므로 복제본 생성 자체로 과거 행을 되살릴 수 없다.'),
('삭제 후 수동 스냅샷만 복원한다','이 스냅샷은 삭제된 상태를 담는다. 삭제 직전 상태를 지정하려면 복구 가능 시간 범위를 확인한다.')],
'PITR은 새 DB 인스턴스를 만든다. 일부 행 복구는 운영 DB와 병합하는 단계까지 계획한다.','AmazonRDS/latest/UserGuide/USER_PIT.html'),
('메시징','주문별 상태 변경 순서를 보존하면서 서로 다른 주문은 병렬 처리해야 한다. 재시도 때 같은 결제가 중복 반영되는 것도 방지하려면?',[
('SQS FIFO에서 주문 ID로 메시지 그룹을 나누고 결제 처리를 멱등하게 만든다','같은 그룹 내 순서와 그룹 간 병렬성을 확보한다. 처리 중 실패 후 재수신해도 결제 키로 중복 반영을 막는다.'),
('표준 큐 하나만 사용한다','표준 큐는 최선형 순서를 제공하므로 같은 주문의 상태 전이가 항상 순서대로 전달된다고 가정할 수 없다.'),
('모든 주문을 단일 FIFO 메시지 그룹에 넣는다','전체 순서가 묶여 서로 다른 주문의 독립적인 병렬 처리 요구에 맞지 않는다.'),
('가시성 제한 시간만 길게 설정한다','동시 재수신 가능성을 낮출 수 있지만 순서 보존과 결제 결과의 중복 방지는 별도로 설계해야 한다.')],
'FIFO 순서 보장의 단위는 MessageGroupId다. 소비자 측 부수 효과에는 멱등성이 필요하다.','AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagegroupid-property.html'),
('공유 스토리지','두 AZ에서 Linux EC2 웹 서버를 자동 확장한다. 기존 프로그램이 같은 경로에서 파일을 수정하므로 POSIX 파일 시스템을 공유해야 한다. 서버를 직접 운영하지 않는 설계는?',[
('Regional EFS와 AZ별 마운트 타깃','동일한 관리형 NFS 파일 시스템에 여러 AZ의 인스턴스가 접근할 수 있다. AZ별 마운트 타깃을 구성한다.'),
('인스턴스별 EBS 볼륨을 같은 경로에 마운트','경로 문자열이 같아도 서로 다른 블록 볼륨이다. 다른 서버의 변경 사항이 공유되지 않는다.'),
('EBS Multi-Attach 볼륨 하나를 두 AZ에 연결','Multi-Attach는 지원 볼륨을 같은 AZ의 여러 인스턴스에 연결한다. 이 구성은 AZ 경계를 넘는다.'),
('각 서버의 인스턴스 스토어에 파일 저장','호스트 로컬 데이터는 다른 서버와 자동 공유되지 않고 인스턴스 수명에도 종속된다.')],
'여러 AZ의 Linux 공유 파일에는 Regional EFS와 마운트 타깃을 함께 고려한다.','efs/latest/ug/accessing-fs.html')]
numeric = list(items)
items.clear()
for question in design:
    add(*question)
for i in range(5):
    if (date.toordinal()+i) % 3:
        items[i] = numeric[i]

archive=root/'archive'
archive.mkdir(exist_ok=True)
file=archive/f'{date}.js'
if not file.exists():
    prior=set()
    for existing in archive.glob('*.js'):
        prior.update(q['stem'] for q in json.loads(existing.read_text().removeprefix('show(').removesuffix(');')))
    if any(q['stem'] in prior for q in items):
        # Repeated numerical exercises are eligible for spaced review.
        for q in items:
            q['review']=q['stem'] in prior
    file.write_text('show('+json.dumps(items,ensure_ascii=False)+');')
dates=sorted((f.stem for f in archive.glob('*.js')),reverse=True)
(root/'dates.js').write_text('const dates='+json.dumps(dates)+';')
