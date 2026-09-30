# 프로젝트 1 · 3-Tier 고가용성 웹 서비스

## 목표와 결과물

**웹·앱·DB를 분리하고, 인스턴스가 교체되어도 데이터를 유지하는 웹 서비스**를 만듭니다. 공통 앱은 Node.js와 PostgreSQL을 사용하는 ‘클라우드 실습 노트’입니다. 저장·목록 API와 인스턴스/버전 표시를 제공해 장애와 배포를 관찰할 수 있습니다.

[전체 코드 ZIP](sample-files/cloud-projects.zip)에는 네 프로젝트의 코드·가이드가 함께 들어 있습니다. 압축을 풀고 `cloud-projects` 폴더에서 명령을 실행하세요. 현재 범위는 로컬 실습이며 AWS 적용은 수행하지 않습니다.

## 구조 — 세 계층과 두 가용 영역

```text
사용자
  ↓
외부 ALB                  public subnet A / C
  ↓
Nginx 웹 EC2 ASG (최소 2)  private web subnet A / C
  ↓
내부 ALB                  private app subnet A / C
  ↓
Node.js 앱 EC2 ASG (최소 2) private app subnet A / C
  ↓
RDS PostgreSQL            isolated DB subnet A / C
  └─ Multi-AZ standby
```

웹은 HTTP 요청을 전달하고, 앱은 입력 검증·SQL 실행을 처리하며, DB는 데이터를 저장합니다. 외부/내부 ALB가 각 대상 그룹의 상태를 확인합니다. 웹·앱 ASG는 CPU 50% 목표 추적 정책으로 2~4대 사이에서 확장합니다. 자동 확장에는 시간이 걸리므로 급격한 트래픽을 무조건 무중단으로 처리한다고 설명하지 않습니다.

## 네트워크와 접근 제어

| 계층 | 들어오는 연결 | 나가는 경로 |
|---|---|---|
| 외부 ALB | allowed_cidr의 80/443 | 웹 SG의 80 |
| 웹 | 외부 ALB SG의 80 | 내부 ALB 80, 패키지 설치용 NAT |
| 내부 ALB | 웹 SG의 80 | 앱 SG의 8080 |
| 앱 | 내부 ALB SG의 8080 | DB 5432, ECR·Secrets Manager 등 NAT |
| DB | 앱 SG의 5432 | 인터넷 기본 경로 없음 |

Terraform의 인바운드는 SG 참조로 제한합니다. 웹/앱의 아웃바운드는 학습 편의상 허용하고 DB는 격리합니다. SSH 포트는 열지 않고 관리 접속에는 SSM을 사용합니다. ALB는 인터넷 진입점이고 NAT는 사설 서버의 외부 요청 경로입니다. NAT는 외부 사용자의 앱 접속 경로가 아닙니다.

## 로컬 실행 — 먼저 요청 흐름 익히기

Docker Desktop을 실행하고 다음을 실행합니다.

```bash
docker compose up -d --build --scale app=2
curl -fsS http://localhost:8088/readyz
curl -fsS http://localhost:8088/api/info
```

브라우저에서 `http://localhost:8088`을 엽니다. 노트를 저장한 뒤 새로고침하면 같은 데이터를 조회합니다. 웹 컨테이너 → 앱 컨테이너 → DB 컨테이너 순서로 전달됩니다. `migrate` 서비스가 먼저 테이블을 생성하고 앱은 준비 상태 검사를 통과해야 웹에 연결됩니다.

로컬 컨테이너 2개는 AWS의 서로 다른 AZ가 아닙니다. 네트워크 구조와 다중 앱의 공용 DB 사용을 연습하는 환경입니다.

## 코드 읽는 순서

| 파일 | 확인할 내용 |
|---|---|
| compose.yaml | 웹·데이터 네트워크, DB 볼륨, 준비 순서 |
| web/default.conf.template | Nginx 프록시, DNS 재조회 |
| app/server.cjs | 입력 검증, 매개변수 SQL, health/ready 분리 |
| infra/modules/network/main.tf | 2 AZ, 계층별 서브넷, NAT·라우팅 |
| infra/modules/database/main.tf | Multi-AZ·백업·암호 관리 |
| infra/modules/vm-tier/main.tf | ASG·Launch Template·CPU 확장 |
| infra/three-tier/main.tf | SG·두 ALB·웹/앱 모듈 연결 |

EC2 앱은 ECR 이미지를 digest로 고정해 실행합니다. user-data는 Docker 설치 → 이미지 받기 → 테이블 마이그레이션 → systemd 서비스 등록 순서입니다. 이미지 준비와 Terraform 변수 입력은 [IaC 가이드](cloud-iac-reference.html)에 있습니다.

## 로컬 장애 실습과 관찰

```bash
docker compose ps
python3 scripts/probe.py http://localhost:8088/api/notes --count 60
```

다른 터미널에서 `docker compose ps -q app`으로 앱 컨테이너 ID 두 개를 확인하고 **하나의 ID만** `docker stop ID`로 중지합니다. 종료·DNS 재조회 사이에 오류가 나타날 수 있으므로 CSV의 실패 요청과 복구 시점을 기록하세요. 이후 `docker compose up -d --scale app=2`로 복구합니다.

DB 장애는 `docker compose stop db` 후 `/readyz`와 목록 요청이 503인지 확인하고 `docker compose start db`로 복구합니다. 이 실습은 단일 DB 중지이며 RDS Multi-AZ failover와 동일하지 않습니다. 멈춘 컨테이너/DB는 다음 실습 전 복구하세요.

## AWS에서 검증할 항목 — 이번에는 미실행

1. ALB 대상 그룹에 두 AZ의 정상 대상이 있는지 확인합니다.
2. 앱 ASG 인스턴스 한 개를 종료한 뒤 대체 인스턴스 생성과 요청 실패율을 기록합니다.
3. 통제한 부하를 점진적으로 늘려 CPU·응답 시간·ASG 개수 변화를 관찰합니다.
4. RDS Multi-AZ 강제 장애조치 전후의 503 구간과 복구 시간을 측정합니다.
5. 백업을 **별도 DB 인스턴스**로 복구하고 노트 데이터의 시점·개수를 대조합니다.

RDS Multi-AZ DB 인스턴스의 standby는 읽기 확장용이 아닙니다. 장애조치 과정에서 연결이 끊길 수 있으며, Multi-AZ와 백업은 각각 가용성과 과거 데이터 복구를 다룹니다. [AWS 공식 Multi-AZ 설명](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html)

## 비용·정리·포트폴리오 기록

EC2 4대 이상, ALB 2개, NAT 2개, Multi-AZ RDS와 스토리지·로그·전송 비용이 발생할 수 있습니다. 단일 NAT로 줄이는 `ha_nat=false`는 비용 실험용이며 AZ 장애에 대한 외부 통신 복원력을 낮춥니다. 무료라고 가정하지 말고 리전별 계산기로 사용 시간과 수량을 계산하세요.

로컬 종료는 `docker compose down`, 데이터까지 초기화하려면 `docker compose down -v`입니다. AWS 삭제 절차는 IaC 가이드를 따릅니다.

포트폴리오는 **구조도 → 요청 경로 → 장애 실험 → 측정값 → 비용·한계 → 개선점**으로 작성합니다. 실제로 측정하지 않은 가용성 수치나 ‘완전 무중단’을 성과로 쓰지 않습니다. [AWS 요금 계산기](https://calculator.aws/) · [EC2 Auto Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html)
