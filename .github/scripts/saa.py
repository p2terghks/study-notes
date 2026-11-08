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

kb=rng.randint(2,15)*4-1
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
