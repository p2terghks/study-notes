# 온프레미스 서버 구축 및 서비스 초기 세팅 가이드

> Ubuntu Server 24.04 LTS · Network · SSH · UFW · Nginx · Spring Boot · PostgreSQL · Docker · Backup · Monitoring  
> 목적: 클라우드 서비스를 사용하지 않고 물리 서버 또는 VM 위에 웹 서비스를 직접 구축하기 위한 단계별 학습 문서.

## 목차

1. 아키텍처와 설계
2. 하드웨어 및 IP 주소 계획
3. Ubuntu Server 설치와 초기 점검
4. Netplan 고정 IP / 라우팅 / DNS
5. 사용자·SSH·방화벽 보안
6. Nginx·Java·PostgreSQL 직접 설치
7. Docker Compose 배포
8. Nginx 리버스 프록시·DNS·HTTPS
9. 로그·모니터링·백업
10. 다중 서버 확장과 장애 점검
11. 최종 체크리스트

---

## 1. 클라우드와 온프레미스 비교

| AWS | 온프레미스에서 구성할 항목 |
|---|---|
| EC2 | 물리 서버 / VM |
| VPC 및 Subnet | 네트워크 대역 / VLAN / 라우팅 |
| Security Group | UFW / 네트워크 방화벽 / ACL |
| EBS | SSD / RAID / 스토리지 |
| RDS | 직접 설치한 PostgreSQL |
| ALB | Nginx / HAProxy |
| CloudWatch | Prometheus / Grafana / 로그 |
| IAM | Linux 계정 / 그룹 / LDAP |
| S3 | NAS / 오브젝트 스토리지 |

**핵심:** 온프레미스는 하드웨어, OS, 네트워크, 백업, 보안, 장애복구를 직접 운영한다.

### 학습용 단일 서버 구성

~~~text
인터넷 사용자
  → 공유기 / 방화벽 / 공인 IP / NAT
  → Ubuntu Server (192.168.10.10)
       → Nginx :80, :443
       → Spring Boot (localhost:8080)
       → PostgreSQL (Docker 내부 :5432)
  → 별도 백업 저장소
~~~

학습용으로 한 대에 구성하되 실제 운영에서는 웹·애플리케이션·DB·백업을 역할별로 분리하는 것이 좋다.

## 2. 하드웨어 및 네트워크 설계

### 권장 학습 사양

| 항목 | 예시 | 목적 |
|---|---|---|
| CPU | 4코어 이상 | API / DB 처리 |
| RAM | 16GB | Java·DB·OS |
| SSD | 256–512GB | 데이터 / OS |
| NIC | 1Gbps | 네트워크 |
| UPS | 권장 | 정전 대응 |
| 스토리지 | SSD + 별도 백업 | 데이터 보호 |

RAID 1/5/6/10은 디스크 장애에 대비하기 위한 기술이지만 **백업을 대체하지 않는다.**

### IP 설계 예시

| 구성 요소 | 값 |
|---|---|
| LAN | 192.168.10.0/24 |
| Gateway | 192.168.10.1 |
| Ubuntu 서버 | 192.168.10.10 |
| 관리자 PC | 192.168.10.100 |
| DNS | 1.1.1.1 / 8.8.8.8 |
| Hostname | onprem-server |

실제 설정 시 공유기 LAN 범위 및 DHCP 할당 범위와 충돌하지 않아야 한다. 서버 주소는 고정 IP 또는 DHCP 예약을 사용한다.

외부 공개가 필요한 경우 공인 IP, CGNAT 여부, 이중 NAT, 포트포워딩, ISP 정책을 사전에 확인한다. 내부 전용 시스템은 VPN/사내망 접근만 허용하는 편이 안전하다.

## 3. Ubuntu Server 설치

1. [Ubuntu Server 공식 다운로드](https://ubuntu.com/download/server)에서 Ubuntu Server 24.04 LTS ISO 다운로드.
2. 설치 USB 또는 VM 가상 광학 드라이브로 부팅.
3. 키보드·언어, 네트워크(처음에는 DHCP 권장), 스토리지, 호스트명, 계정 설정.
4. OpenSSH Server 설치 체크.
5. 재부팅 후 로그인.

**주의:** 설치 프로그램에서 디스크 전체 사용을 선택하면 기존 데이터가 삭제될 수 있다.

~~~bash
cat /etc/os-release
uname -r
lscpu
free -h
df -h
ip -br addr
ip route
~~~

업데이트 및 기본 도구 설치:

~~~bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y curl wget vim git htop dnsutils traceroute ca-certificates openssh-server
~~~

## 4. Netplan으로 고정 IP 구성

현재 인터페이스와 기존 설정을 확인한다.

~~~bash
ip -br addr
ip route
ls -l /etc/netplan/
resolvectl status
~~~

Netplan 파일은 설치 환경마다 이름이 다르다. cloud-init이 관리하는 경우 자동 재작성 여부를 확인하고, 동일 NIC에 충돌하는 설정 파일을 두지 않는다.

예시 설정 (실제 NIC 이름을 확인해 교체):

~~~yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp3s0:
      dhcp4: false
      addresses:
        - 192.168.10.10/24
      routes:
        - to: default
          via: 192.168.10.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
~~~

원격 SSH 접속 중에는 네트워크 변경으로 접속이 끊길 수 있다. 가능하면 물리/가상 콘솔을 확보한 후:

~~~bash
sudo netplan generate
sudo netplan try
sudo netplan apply
ip addr
ip route
ping -c 4 192.168.10.1
ping -c 4 1.1.1.1
getent hosts google.com
~~~

- 게이트웨이 통신 실패: 케이블, 서브넷, VLAN, NIC
- 게이트웨이는 성공, 외부 IP 실패: 기본 경로, 라우터, ISP
- 외부 IP 성공, 도메인 실패: DNS

[Ubuntu 네트워크 설정 문서](https://ubuntu.com/server/docs/configuring-networks/)

## 5. Linux 계정 / SSH / 보안

### 관리자 계정

~~~bash
sudo adduser deployadmin
sudo usermod -aG sudo deployadmin
groups deployadmin
~~~

root로 상시 작업하지 말고 필요한 명령에만 sudo를 사용한다.

### SSH 서버

~~~bash
sudo systemctl enable --now ssh
sudo systemctl status ssh
~~~

관리자 PC에서:

~~~bash
ssh deployadmin@192.168.10.10
ssh-keygen -t ed25519 -C "onprem-admin"
ssh-copy-id deployadmin@192.168.10.10
ssh -i ~/.ssh/id_ed25519 deployadmin@192.168.10.10
~~~

개인키는 공유하지 않는다. **키 인증을 별도 터미널에서 확인한 후** SSH 암호 인증을 끈다.

`/etc/ssh/sshd_config.d/99-hardening.conf`:

~~~text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
~~~

~~~bash
sudo sshd -t
sudo systemctl reload ssh
~~~

### UFW 기본 규칙

~~~bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.10.100 to any port 22 proto tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status numbered
~~~

| 포트 | 서비스 | 접근 정책 |
|---|---|---|
| 22 | SSH | 관리 PC / VPN만 |
| 80 / 443 | HTTP(S) | 공개 웹인 경우만 |
| 8080 | Spring Boot | 로컬 / 내부만 |
| 5432 | PostgreSQL | DB 클라이언트 제한 |
| 6379 | Redis | 외부 공개 금지 |
| 9090 / 3000 | 모니터링 | 관리망만 |

**Docker의 게시된 포트는 UFW와 별도의 네트워크 정책을 따른다.** 컨테이너 `ports`에 DB나 Redis를 `0.0.0.0`으로 게시하지 않는다.

보안 업데이트:

~~~bash
sudo apt install unattended-upgrades -y
~~~

운영에서는 패키지 업데이트에 따른 서비스 영향과 재부팅 정책을 별도 점검한다.

## 6. 직접 설치 방식: Nginx, Java, PostgreSQL

~~~bash
sudo apt install -y nginx openjdk-21-jre-headless postgresql postgresql-contrib
sudo systemctl enable --now nginx postgresql
sudo nginx -t
java -version
sudo ss -lntp
~~~

Nginx 기본 응답:

~~~bash
curl -I http://127.0.0.1
~~~

PostgreSQL 역할 및 DB 생성:

~~~bash
sudo -u postgres psql
~~~

~~~sql
CREATE USER appuser WITH PASSWORD 'REPLACE_WITH_STRONG_PASSWORD';
CREATE DATABASE appdb OWNER appuser;
~~~

~~~text
\q
~~~

이후 Docker 구성으로 전환한다면 기존 호스트 PostgreSQL과 컨테이너 PostgreSQL의 **데이터, 포트, 백업 정책을 혼동하지 않도록** 한다.

## 7. Docker 방식 서비스 배포

Docker Engine은 [공식 Ubuntu 설치 가이드](https://docs.docker.com/engine/install/ubuntu/)에 따라 설치한다.

~~~bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
~~~

~~~bash
sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
~~~

~~~bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
~~~

Docker 관리 권한은 사실상 강력한 호스트 권한에 해당하므로 docker 그룹에 무분별하게 사용자를 추가하지 않는다.

### 파일 구조

~~~text
/opt/onprem-app/
├── compose.yaml
├── .env
├── .gitignore
└── backend/
    ├── Dockerfile
    ├── build.gradle
    ├── settings.gradle
    ├── gradlew
    ├── gradle/
    └── src/
~~~

**backend/Dockerfile** — 실행 가능한 JAR가 하나만 생성되는 Gradle Spring Boot 예시:

~~~dockerfile
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /app
COPY . .
RUN chmod +x ./gradlew
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
~~~

**compose.yaml** — Nginx는 호스트에서 실행하고 backend/db만 컨테이너로 실행한다.

~~~yaml
services:
  backend:
    build: ./backend
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/appdb
      SPRING_DATASOURCE_USERNAME: appuser
      SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
    depends_on:
      db:
        condition: service_healthy
    networks: [app-network]

  db:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [app-network]

networks:
  app-network:
    driver: bridge

volumes:
  postgres-data:
~~~

**.env** (절대 커밋하지 않기):

~~~dotenv
DB_PASSWORD=REPLACE_WITH_A_LONG_RANDOM_SECRET
~~~

**.gitignore**:

~~~gitignore
.env
.env.*
!.env.example
*.log
~~~

~~~bash
chmod 600 .env
sudo docker compose config --quiet
sudo docker compose up -d --build
sudo docker compose ps
sudo docker compose logs -f backend
curl -i http://127.0.0.1:8080
~~~

`404`가 나와도 API의 `/` 라우트가 없을 뿐일 수 있다. 실제 구현된 엔드포인트로 확인한다.

데이터 보존: `docker compose down`은 기본적으로 볼륨을 유지하지만, **`down -v`는 데이터 볼륨 삭제 위험**이 있다.

## 8. Nginx 리버스 프록시·도메인·HTTPS

`/etc/nginx/sites-available/onprem-app`:

~~~nginx
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
}
~~~

~~~bash
sudo ln -s /etc/nginx/sites-available/onprem-app /etc/nginx/sites-enabled/onprem-app
sudo nginx -t
sudo systemctl reload nginx
curl -H "Host: app.example.com" http://127.0.0.1/
~~~

도메인 DNS A 레코드에서 `app.example.com`을 라우터의 실제 공인 IPv4로 연결하고, 필요한 경우 라우터에서 TCP 80/443을 웹 서버로 포워딩한다. `app.example.com`은 예시 도메인이다.

외부 인증 조건을 충족한 실제 도메인에 대해:

~~~bash
sudo snap install --classic certbot
sudo certbot --nginx -d app.example.com
sudo certbot renew --dry-run
~~~

[Certbot](https://certbot.eff.org/)의 HTTP-01 방식은 일반적으로 외부 TCP 80 접근이 필요하다. 외부 비공개 서비스는 내부 CA 또는 DNS-01 방식을 검토한다.

## 9. 운영 로그·모니터링·백업

### 자주 쓰는 점검 명령어

~~~bash
htop
free -h
df -h
sudo ss -lntp
sudo journalctl -u ssh -n 100
sudo journalctl -b
sudo tail -f /var/log/nginx/error.log
sudo docker compose stats
sudo docker compose logs --tail=100 backend
~~~

모니터링 확장:

~~~text
Node Exporter / 애플리케이션 메트릭
  → Prometheus
  → Grafana
  → 대시보드 / 장애 알림
~~~

### PostgreSQL 백업·복원 예시

Compose 프로젝트 디렉터리에서 실행:

~~~bash
mkdir -p ~/backups
sudo docker compose exec -T db pg_dump -U appuser -d appdb -Fc > ~/backups/appdb.dump
ls -lh ~/backups/appdb.dump
~~~

별도의 테스트 DB에서 복원 테스트:

~~~bash
sudo docker compose exec -T db createdb -U appuser restoretest
sudo docker compose exec -T db pg_restore -U appuser -d restoretest --no-owner < ~/backups/appdb.dump
~~~

주의사항:
- 단일 서버 디스크에만 백업을 보관하지 않는다.
- NAS/별도 저장소/오프라인 저장소를 이용한다.
- 백업 암호화 및 접근권한을 관리한다.
- DB 역할, 확장, 스키마, 글로벌 객체, 버전 호환성을 별도 확인한다.
- 매일 백업이 성공했는지 확인하고 정기적으로 복원 테스트한다.
- RPO(허용 데이터 손실량)와 RTO(목표 복구 시간)에 따라 정책을 정한다.

## 10. 다중 서버 확장 설계

| 영역 | 네트워크 예시 | 구성 |
|---|---|---|
| 관리망 | 192.168.10.0/24 | 관리자/VPN |
| DMZ | 192.168.20.0/24 | WEB01 / Nginx |
| APP | 192.168.30.0/24 | APP01 / APP02 |
| DB | 192.168.40.0/24 | DB01 / PostgreSQL |
| Backup | 192.168.50.0/24 | 백업 서버 |

허용 정책 예시:

| 출발지 | 목적지 | 포트 |
|---|---|---|
| 인터넷 | WEB | TCP 443 |
| WEB | APP | TCP 8080 |
| APP | DB | TCP 5432 |
| 관리자 VPN | 서버 관리망 | TCP 22 |
| 인터넷 | DB | 차단 |

IP 대역을 구분하는 것만으로 격리되지 않는다. VLAN·L3 라우팅·방화벽 ACL 등을 함께 설정한다.

가상화 환경은 KVM/Proxmox 등을 사용할 수 있다.

~~~text
물리 서버 → Hypervisor
             ├─ WEB VM
             ├─ APP VM
             ├─ DB VM
             └─ Monitoring VM
~~~

단일 물리 호스트는 단일 장애점(SPOF)이 될 수 있으므로 고가용성 요구가 있으면 복수 호스트와 페일오버를 설계한다.

CI/CD의 기본 흐름은 `Git Push → 테스트/빌드 → 이미지 Registry → 온프레미스 서버 Pull → 배포 및 롤백`이다.

## 11. 장애 발생 시 점검 순서

1. 물리 서버 전원 / NIC / 케이블
2. OS 부팅 및 CPU/메모리/디스크
3. IP / DNS / Gateway / 라우트
4. 방화벽 / NAT / 서비스 포트
5. Nginx 상태 및 에러 로그
6. Spring Boot 컨테이너 상태 및 로그
7. DB 상태와 연결
8. 장애 원인 수정 후 정상 요청 및 복구 검증

| 증상 | 먼저 확인할 항목 |
|---|---|
| SSH 실패 | IP, sshd, UFW, VPN |
| 도메인 접속 실패 | DNS, NAT, 방화벽 |
| 502 Bad Gateway | proxy_pass, backend 상태, 8080 |
| DB 연결 오류 | DB 컨테이너, 자격증명, Docker 네트워크 |
| 디스크 부족 | df, 로그/볼륨 |
| 컨테이너 재시작 반복 | compose logs |

## 12. 최종 실습 체크리스트

- [ ] 물리 서버/VM 준비
- [ ] Ubuntu Server 설치 및 OS 업데이트
- [ ] LAN 대역, 게이트웨이, DNS 계획
- [ ] 서버 고정 IP 적용 및 통신 검증
- [ ] 관리자 계정과 SSH 키 인증
- [ ] 방화벽 최소 허용 규칙
- [ ] Nginx, Docker Engine 및 Compose 설치
- [ ] Spring Boot + PostgreSQL 구성
- [ ] DB 볼륨 / 시크릿 관리
- [ ] Reverse Proxy 요청 테스트
- [ ] DNS, HTTPS 인증서 및 갱신
- [ ] 로그 / CPU·메모리·디스크 모니터링
- [ ] 백업 / 실제 복원 테스트
- [ ] 장애 복구 / 롤백 절차 문서화

---

## 참고 링크

- [Ubuntu Server](https://ubuntu.com/download/server)
- [Ubuntu 네트워크 설정](https://ubuntu.com/server/docs/configuring-networks/)
- [Docker Engine 설치](https://docs.docker.com/engine/install/ubuntu/)
- [Nginx 문서](https://nginx.org/en/docs/)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
- [Certbot](https://certbot.eff.org/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

> **실습 노트:** 모든 IP, 사용자명, 도메인, 비밀번호는 예시다. 실서비스에 적용하기 전 환경에 맞춰 변경하고, SSH·방화벽·DB 설정 시 콘솔 복구 수단과 백업을 준비한다.
