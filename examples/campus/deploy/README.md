# AWS ECS Fargate + RDS 배포

배포 코드를 준비한 상태입니다. 아래 명령은 실제 AWS 리소스와 비용을 발생시킵니다. 현재 계정에 실행하지 않았습니다.

## 구성

```text
도메인 → ALB (ACM HTTPS, HTTP→HTTPS)
             ↓ 보안 그룹에서 8080 허용
         Fargate 2개 (서로 다른 가용 영역의 private subnet)
             ↓ TLS 인증서 검증, PostgreSQL 5432
         RDS PostgreSQL (private, 암호화, Multi-AZ)
             ├─ 학생 / 강의 / 신청 / 장바구니
             └─ Spring Session 공용 로그인 세션

ECR → 이미지 / Secrets Manager → DB 자격증명 / CloudWatch → 로그
```

- `ecs-fargate.json`: VPC, public/private 서브넷 각 2개, NAT Gateway 2개, 보안 그룹, RDS, Secrets Manager, ECR, ECS, ALB, IAM, 로그 그룹.
- `deploy.sh infra`: 기반 리소스만 생성. `ImageUri`가 비어 있으면 ECS 서비스는 생성하지 않습니다.
- `deploy.sh app`: amd64 Docker 이미지 빌드·ECR 업로드 후 Fargate 서비스를 생성/갱신합니다.
- `bootstrap-db.sql`: 최초 1회 제한된 애플리케이션 DB 계정 생성. RDS 관리자 자격증명은 앱에 주입하지 않습니다.
- `check-container.py`: 실제 이미지로 앱 2개를 동시에 시작해 Flyway 초기화와 컨테이너 간 로그인 세션 공유를 검사합니다. 임시 DB/네트워크만 사용하고 자동 정리합니다.
- `check-postgres.sh`: 임시 PostgreSQL 컨테이너에서 통합·동시성·세션 테스트. 종료 시 해당 컨테이너를 정리합니다.

기본값은 Fargate 태스크 2개(각 0.5 vCPU/1GB), RDS `db.t4g.micro` Multi-AZ, 암호화된 gp3 20GB(최대 자동 확장 100GB), 백업 7일, 로그 30일입니다. 리전의 인스턴스 지원/서비스 할당량을 확인하세요. 태스크 수와 DB 인스턴스 설정은 환경변수로 변경할 수 있습니다. 자동 스케일링 정책은 아직 포함하지 않았습니다.

**ALB, Fargate, RDS, NAT Gateway 2개, 공인 IPv4, 로그/비밀 저장소 등에 지속 비용이 발생합니다.** 비용 검토 후 실행하세요. NAT는 private 태스크의 ECR 이미지·Secrets Manager·CloudWatch 접근에 사용합니다.

## 1. 준비

- AWS CLI v2로 원하는 계정에 로그인(`aws sso login` 등). AWS 키를 코드나 채팅에 넣지 마세요.
- Docker Desktop 또는 Docker Engine + Buildx.
- 소유 도메인과 **배포 리전에서 발급 완료된 ACM 인증서**.
- CloudFormation에서 VPC·RDS·ECS·ECR·ALB·IAM·Secrets Manager·CloudWatch를 생성할 수 있는 배포 권한.
- 기존 로컬 H2 데이터는 이 배포에 자동 복사되지 않습니다.

프로젝트 루트에서:

```sh
export AWS_REGION=ap-northeast-2
export STACK_NAME=campus-prod
export CERTIFICATE_ARN=arn:aws:acm:ap-northeast-2:123456789012:certificate/REPLACE_ME
# 선택값: 후속 배포에서도 유지하세요.
export DESIRED_COUNT=2
export DATABASE_MULTI_AZ=true
export DATABASE_CLASS=db.t4g.micro

aws sts get-caller-identity
./deploy/deploy.sh infra
```

이 작업은 RDS 생성 때문에 시간이 걸립니다. 인프라 생성 직후에는 서비스가 없으므로 ALB가 503을 반환하는 것이 정상입니다. `infra` 명령은 기존 스택 위에서 실행되지 않도록 막았습니다. 후속 변경은 `app` 단계 또는 ImageUri를 유지한 CloudFormation 변경 세트를 사용하세요.

## 2. 최초 애플리케이션 DB 계정 생성

CloudFormation Outputs에서 다음 값을 확인하세요.

- `DatabaseEndpoint`: RDS 주소
- `AdminSecretArn`: RDS가 관리하는 `campus_admin` 비밀정보
- `AppSecretArn`: 자동 생성된 `campus_app` 비밀정보
- `VpcId`, `PrivateSubnet1`, `AppSecurityGroupId`: DB 초기화용 접속 환경

AWS CloudShell의 **VPC 환경**을 해당 VPC·private subnet·AppSecurityGroup으로 생성하거나, 동일 네트워크에 접속 가능한 관리 호스트에서 작업합니다. PostgreSQL 클라이언트 `psql`을 준비하세요. 일반 CloudShell이나 개인 노트북에서는 private RDS에 직접 연결할 수 없습니다.

```sh
curl --fail --location https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o global-bundle.pem
psql "host=RDS_ENDPOINT port=5432 dbname=campus user=campus_admin sslmode=verify-full sslrootcert=global-bundle.pem" -W
```

Secrets Manager 콘솔에서 `AdminSecretArn`의 비밀번호를 확인하고 `psql` 비밀번호 프롬프트에 입력합니다. `deploy/bootstrap-db.sql`을 관리 환경에 가져온 뒤 psql 안에서 실행합니다.

```sql
\i bootstrap-db.sql
\password campus_app
```

비밀번호 프롬프트에는 **AppSecretArn의 password 값**을 입력합니다. SQL이나 셸 명령에 실제 비밀번호를 적지 않습니다. `campus_app`은 public 스키마의 객체 생성 권한만 갖고, Flyway가 앱·세션 테이블을 이 계정 소유로 만듭니다. 초기화 후 관리 호스트/CloudShell VPC 환경은 종료하세요.

## 3. 이미지와 서비스 배포

로컬 프로젝트 루트에서:

```sh
export IMAGE_TAG=release-20260918-1
./deploy/deploy.sh app
```

태그는 매번 새 값으로 지정합니다(ECR 불변 태그). 로컬이 Apple Silicon이어도 `linux/amd64`로 빌드됩니다. 이미지 빌드 중 React 테스트·Vite 빌드와 Java 기본 테스트를 실행하며, PostgreSQL 전용 테스트는 아래 검증 명령으로 별도 실행합니다.

앱이 시작되면 Flyway가 `V1`(앱 테이블), `V2`(세션 테이블)를 한 번씩 적용합니다. 여러 태스크가 동시에 시작해도 Flyway가 마이그레이션 잠금을 조정합니다. 기존 마이그레이션 파일은 수정하지 말고 이후 변경은 `V3__...sql`로 추가하세요. 기존 비어 있지 않은 DB에는 별도의 마이그레이션 계획이 필요하며 강제 baseline은 설정하지 않았습니다.

ALB `/actuator/health/readiness`는 DB까지 확인합니다. 정상 태스크로 교체하지 못하면 ECS 배포 회로 차단기가 이전 정상 배포로 롤백합니다(최초 배포에는 이전 버전이 없습니다). 애플리케이션 롤백이 DB 스키마를 되돌리지는 않으므로 이후 DB 변경은 이전 앱과 호환되게 작성하세요.

## 4. 도메인 연결 및 확인

Route 53에서 인증서와 일치하는 도메인의 A Alias를 `LoadBalancerDns`/`LoadBalancerHostedZoneId`의 ALB로 연결하세요. 외부 DNS의 서브도메인은 ALB DNS를 대상으로 CNAME을 설정할 수 있습니다. ALB 자체 DNS 이름은 사용자 인증서와 다르므로 서비스 접속에는 인증서 도메인을 사용하세요.

```sh
curl --fail https://YOUR_DOMAIN/actuator/health/readiness
```

`{"status":"UP"...}` 및 HTTP 200을 확인하고, 브라우저에서 회원가입 → 로그인 → 페이지 새로고침 → 로그아웃을 확인합니다. 운영에서는 체험 계정·강의 자동 생성 및 체험 로그인 버튼이 꺼져 있습니다. **초기 강의는 비어 있으므로 실제 강의/수업 시간 데이터를 별도로 입력해야 수강신청을 사용할 수 있습니다.** 관리자 강의 관리 UI는 아직 없습니다.

학번 회원가입은 현재 자체 가입 방식입니다. 실제 학사 서비스로 공개하기 전에는 학적 시스템/학교 인증에 맞춘 가입 정책과 수강 기간을 적용해야 합니다.

## 변경·운영

- 재배포: 새 `IMAGE_TAG`로 `./deploy/deploy.sh app`.
- 세션: PostgreSQL에서 공유하므로 요청이 다른 태스크로 이동하거나 태스크가 재시작해도 로그인 상태를 유지합니다(30분 만료). ALB 고정 세션이 필요하지 않습니다.
- 동시 신청: 사용자 → 강의 순서의 DB 행 잠금을 그대로 사용하여 여러 서버에서도 정원/학점/시간 충돌을 검사합니다.
- TLS: HTTPS Secure/HttpOnly/SameSite=Lax 세션 쿠키. ALB만 앱 포트에 접근하며 RDS 서버 인증서를 `verify-full`로 검증합니다.
- 비밀번호 변경: DB 사용자 비밀번호와 AppSecret 값을 함께 변경한 뒤 ECS 새 배포를 실행해야 합니다. 이미 실행 중인 태스크에 새 secret이 자동 반영되지 않습니다. 자동 DB 비밀번호 회전은 구성하지 않았습니다.
- 로그: 출력된 `LogGroupName`에서 부팅 실패, DB 접속, Flyway 오류를 확인합니다. DB 비밀번호/세션 값을 로깅하지 마세요.
- 태스크 수 증가: RDS 연결 수를 점검하세요. 기본 태스크당 최대 10개 연결이며 롤링 배포 때 태스크가 최대 2배 실행될 수 있습니다.
- 정리: RDS 삭제 방지가 활성화되어 있어 스택 삭제 전 별도로 해제해야 합니다. RDS는 삭제 시 스냅샷을 남기고, ECR/앱 Secret/로그는 Retain으로 남습니다. 자동으로 전부 삭제되지 않으므로 백업 보존 및 잔여 비용을 확인하세요.

## 검증 결과 (2026-09-18)

- H2 10개 + PostgreSQL 11개 통합 테스트 통과(실패/건너뜀 0). PostgreSQL은 관리자 권한이 없는 `campus_app` 계정으로 실행했습니다.
- `cfn-lint`와 배포 셸 스크립트 구문 검사 통과.
- `linux/amd64` Docker 이미지 빌드 및 빌드 단계의 Java 17 테스트 통과.
- 실제 앱 컨테이너 2개와 PostgreSQL에서 동시 Flyway 초기화, 헬스 체크, 회원가입·로그인, Secure 쿠키, 컨테이너 간 로그인 세션 공유, 체험 데이터 비활성화 확인.
- 실제 AWS 계정에서의 리소스 생성·ACM 인증서·RDS TLS 연결·도메인 접속은 아직 실행하지 않았습니다. 로컬 컨테이너 검증은 격리 네트워크 내 PostgreSQL에 한해 TLS 없이 수행했습니다.

## 로컬 검증

```sh
./mvnw test
./deploy/check-postgres.sh
cfn-lint deploy/ecs-fargate.json
bash -n deploy/deploy.sh deploy/check-postgres.sh
docker buildx build --platform linux/amd64 --load -t campus:ecs-check .
python3 deploy/check-container.py campus:ecs-check
```

PostgreSQL 테스트는 DB 데이터를 삭제하므로 **운영 DB의 접속정보를 TEST_POSTGRES_*에 넣지 마세요.** 제공 스크립트는 임시 컨테이너만 사용합니다. cfn-lint와 로컬 테스트는 실제 AWS 리소스 생성 성공이나 계정 할당량을 보장하지 않습니다.

공식 문서: [ECS Secrets Manager 주입](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html), [RDS PostgreSQL TLS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html), [Spring Session JDBC](https://docs.spring.io/spring-session/reference/configuration/jdbc.html).
