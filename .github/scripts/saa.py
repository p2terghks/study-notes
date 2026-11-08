"""Generate a reproducible daily set using curated architecture scenarios."""
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

# Each case changes the decisive requirement. Explanations identify the
# capability of each alternative and connect it to this specific workload.
families = [
 ('스토리지 비용','AmazonS3/latest/userguide/storage-class-intro.html',[
 ('S3 Glacier Deep Archive','가장 낮은 장기 보관 비용을 우선하고 복원에 시간을 허용하는 자료에 적합하다.','보험사는 감사 자료를 7년 보관한다. 조회는 연 1회 미만이며 복원에 이틀이 걸려도 된다. 보관 단가를 우선하면 어떤 S3 클래스를 선택해야 하는가?','장기 보관 단가가 우선이고 이틀의 복원 시간을 허용한다'),
 ('S3 Glacier Instant Retrieval','분기 단위로 드물게 조회하면서도 사전 복원 없이 밀리초 단위로 접근할 수 있다.','병원은 대용량 영상 원본을 수년간 보관한다. 대부분 분기 한 번 이하로 열지만 응급 조회 때 즉시 읽어야 한다. 접근 빈도가 알려진 이 데이터에 맞는 아카이브 클래스는?','드문 조회와 밀리초 접근을 동시에 요구한다'),
 ('S3 Intelligent-Tiering','객체별 접근 패턴을 관찰해 자동으로 액세스 계층을 조정한다.','미디어 회사는 수백만 개의 대용량 영상을 보관한다. 어떤 영상이 다시 유행할지 예측할 수 없고, 담당자가 전환 규칙을 관리하기 어렵다. 접근 패턴에 맞춰 자동으로 비용을 조정하려면?','객체마다 예측하기 어려운 접근 변화에 자동 대응해야 한다'),
 ('S3 One Zone-IA','재생성 가능한 데이터를 단일 AZ에 보관해 다중 AZ 저빈도 계층보다 저장 비용을 줄인다.','서비스가 원본에서 다시 생성할 수 있는 썸네일 묶음을 보관한다. 드물게 요청되지만 즉시 읽어야 하며 AZ 상실 시 재생성을 허용한다. 단일 AZ 저빈도 계층을 활용하려면?','재생성이 가능하고 단일 AZ 저빈도 저장을 명시한다')]),
 ('데이터베이스','AmazonRDS/latest/UserGuide/Welcome.html',[
 ('RDS Multi-AZ DB 인스턴스 배포','다른 AZ에 동기식 대기 복제본을 두고 장애 시 자동으로 전환한다.','단일 AZ의 RDS for PostgreSQL을 쓰는 예약 서비스가 AZ 장애 시 쓰기를 자동 재개해야 한다. 기존 엔진과 애플리케이션 연결 주소를 유지하려면?','AZ 장애 후 자동 쓰기 장애 조치가 우선이다'),
 ('읽기 전용 복제본으로 조회 분산','비동기 복제본에 조회를 보내 원본 DB의 읽기 부하를 줄인다.','RDS for PostgreSQL에서 대시보드 조회 때문에 결제 쓰기가 느려졌다. 대시보드는 수 초 전 데이터를 허용하며 쿼리 대상을 바꿀 수 있다. 읽기 부하를 어떻게 분리해야 하는가?','조금 늦은 데이터를 허용하면서 조회 작업을 원본에서 분리해야 한다'),
 ('RDS Proxy로 연결 풀링','애플리케이션 연결을 관리하고 데이터베이스 연결을 재사용한다.','수천 개의 짧은 Lambda 실행이 RDS for PostgreSQL에 접속한다. DB CPU는 여유가 있지만 연결 생성과 최대 연결 수가 병목이다. 애플리케이션에 직접 풀을 구현하지 않으려면?','병목은 쿼리 처리량이 아니라 짧은 DB 연결의 폭증이다'),
 ('자동 백업에서 시점 복구','복구 가능 기간 안에서 원하는 시점의 데이터베이스를 새 인스턴스로 복원한다.','담당자가 RDS 테이블을 잘못 갱신했다. 자동 백업이 활성화되어 있고 사고 직전 상태를 별도 DB에서 조사해야 한다. 어떤 방식을 선택해야 하는가?','사고 이전의 특정 시점 데이터를 따로 복구해야 한다')]),
 ('컴퓨팅 비용','AWSEC2/latest/UserGuide/instance-purchasing-options.html',[
 ('EC2 Spot 인스턴스','남는 EC2 용량을 할인받아 쓰며 중단과 재시도를 고려해 설계한다.','렌더링 작업을 조각별로 큐에 저장한다. 중단된 작업은 재개할 수 있고 마감 시간도 유연하다. 장기 약정 없이 컴퓨팅 비용을 줄이려면?','중단 허용과 재시도 가능성이 비용 최적화의 핵심이다'),
 ('Compute Savings Plans','일정한 시간당 사용 금액을 약정해 다양한 컴퓨팅 사용량에 할인을 적용한다.','기업이 수년간 일정한 컴퓨팅 사용 금액을 예상한다. EC2 인스턴스 패밀리와 리전을 바꾸고 일부를 Fargate로 이전해도 할인을 이어가려면?','인스턴스 유형 변경과 Fargate 전환을 포괄하는 사용 약정이 필요하다'),
 ('온디맨드 용량 예약','지정한 AZ에서 일치하는 EC2 인스턴스 속성에 대한 용량을 확보한다.','행사 당일 특정 AZ에서 지정 인스턴스 유형을 반드시 시작해야 한다. 팀의 우선순위는 할인보다 용량 확보이고 장기 사용 약정은 어렵다. 어떤 구성이 적합한가?','특정 AZ의 시작 가능 용량을 확보해야 한다'),
 ('온디맨드 인스턴스','중단 가능한 잉여 용량이나 장기 사용 약정에 의존하지 않고 사용한 만큼 지불한다.','이틀 동안만 실행하는 시험 환경이다. 작업을 Spot 회수로 중단할 수 없고 약정 할인도 필요 없다. 특정 AZ 용량을 미리 확보할 요구가 없을 때 가장 단순한 구매 방식은?','단기 실행이고 약정과 Spot 중단을 모두 피해야 한다')]),
 ('보안 설계','AmazonS3/latest/userguide/security-best-practices.html',[
 ('S3 Object Lock 규정 준수 모드','보존 중인 객체 버전은 루트 사용자를 포함해 누구도 보존 기간 전에 영구 삭제할 수 없다.','감사팀은 결제 증빙의 특정 버전을 5년간 보관해야 한다. 관리자도 기간을 줄이거나 해당 버전을 영구 삭제할 수 없게 하려면?','관리자까지 포함한 변경 불가능한 보존 기간이 필요하다'),
 ('S3 버전 관리','덮어쓰기 전 객체 버전을 유지해 이전 내용을 복구할 수 있다.','편집자가 같은 키에 파일을 자주 덮어쓴다. 방금 덮어쓴 파일을 이전 판으로 복구하고 싶지만 법적 보존 기간이나 삭제 금지는 필요 없다. 최소 기능은?','정상적인 수정은 허용하면서 이전 판을 회수해야 한다'),
 ('S3 Block Public Access','공개 ACL과 공개 정책이 버킷을 인터넷에 노출시키는 경로를 제한한다.','개발자가 공개 ACL이나 공개 버킷 정책을 실수로 적용하더라도 계정의 S3 버킷이 공개되지 않게 하려 한다. 어떤 계정 수준 제어가 적합한가?','공개 ACL 및 정책에 의한 인터넷 노출을 차단해야 한다'),
 ('SSE-KMS와 고객 관리형 키','키 정책을 관리하고 KMS를 통한 키 사용을 감사할 수 있다.','기밀 객체를 암호화하고 보안팀이 키 권한과 비활성화 시점을 직접 통제해야 한다. 데이터 키 사용에 대한 감사도 필요하다. 어떤 암호화 설계인가?','보안팀이 암호화 키의 사용 권한과 수명 주기를 통제해야 한다')]),
 ('애플리케이션 통합','decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html',[
 ('SQS 표준 큐와 경쟁 소비자','큐에 적재된 작업을 여러 소비자가 나누어 처리하며 소비자 장애 동안에도 작업을 보관한다.','이미지 변환 요청이 순간적으로 폭증한다. 요청 순서는 중요하지 않고 각 작업은 한 워커가 처리하면 된다. 멱등한 워커가 따라잡을 때까지 요청을 보관하려면?','여러 워커가 하나의 작업 적체를 나누어 처리해야 한다'),
 ('SNS 주제와 구독자별 SQS 큐','각 구독자에게 이벤트 사본을 전달하고 구독자마다 독립적으로 보관·재시도한다.','신규 가입 이벤트를 분석팀과 메일팀 모두가 받아야 한다. 메일 시스템이 멈춰도 분석은 계속하고 메일팀은 복구 후 밀린 이벤트를 처리하려면?','각 팀에 독립적인 사본과 적체 처리가 필요하다'),
 ('EventBridge 이벤트 버스와 규칙','이벤트의 소스와 세부 필드에 맞는 규칙을 적용해 여러 대상으로 전달한다.','여러 AWS 계정의 서비스 이벤트를 중앙 버스에 수집한다. 이벤트 소스와 상세 상태가 일치할 때만 담당 팀의 대상으로 전달하려면?','중앙 버스에서 이벤트 필드를 기준으로 라우팅해야 한다'),
 ('SQS FIFO와 계좌별 메시지 그룹','같은 그룹의 메시지 순서를 보존하고 다른 그룹은 독립적으로 처리할 수 있다.','계좌별 상태 갱신은 접수 순서를 지켜야 하지만 서로 다른 계좌는 병렬 처리해야 한다. 멱등 처리를 이미 구현한 소비자 앞에 어떤 구조를 두어야 하는가?','순서 보장 범위를 개별 계좌로 한정해야 한다')])
]

for domain, doc, cases in families:
    for answer, explanation, stem, requirement in cases:
        choices = [(answer, explanation)]
        for other, capability, _, _ in cases:
            if other != answer:
                choices.append((other, f'{capability} 이 사례에서는 {requirement}. 이 선택지만으로 그 요구를 충족하지 못한다.'))
        design.append((domain, stem, choices, explanation, doc))

archive = root / 'archive'
edition = archive / f'{date}.js'
if not edition.exists():
    previous = {}
    for path in sorted(archive.glob('????-??-??.js')):
        for question in json.loads(path.read_text().removeprefix('show(').removesuffix(');')):
            previous[question['stem']] = path.stem
    rng.shuffle(design)
    design.sort(key=lambda case: previous.get(case[1], ''))
    domains = set()
    for case in design:
        if case[0] in domains:
            continue
        add(*case)
        items[-1]['review'] = case[1] in previous
        domains.add(case[0])
        if len(items) == 5:
            break
    assert len(items) == 5
    for question in items:
        assert len(question['options']) == 4
        assert sum(correct for _, _, correct in question['options']) == 1
    edition.write_text('show('+json.dumps(items,ensure_ascii=False)+');')
dates = sorted((p.stem for p in archive.glob('????-??-??.js')), reverse=True)
(root/'dates.js').write_text('const dates='+json.dumps(dates+['2026-11-08-calculation'])+';')
