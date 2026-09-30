# Docker 사용법 요약

## 이미지·컨테이너·Dockerfile

**Docker는 앱과 실행에 필요한 환경을 이미지로 묶고 컨테이너로 실행합니다.** GitHub는 주로 코드·협업, 이미지 레지스트리는 배포용 이미지 저장을 맡습니다.

| 용어 | 쉽게 설명하면 |
|---|---|
| Image | 실행 환경과 파일의 템플릿 |
| Container | 이미지로 실행한 개별 인스턴스 |
| Dockerfile | 이미지를 만드는 명령 파일 |
| Registry | 이미지 저장·배포 서버, Docker Hub·ECR·GHCR 등 |
| Volume | 컨테이너와 수명이 분리된 데이터 저장 공간 |
| Compose | 서비스·네트워크·볼륨을 YAML로 선언하는 도구 |

```text
소스 + Dockerfile → docker build → 이미지
이미지 → docker run → 컨테이너
이미지 → docker push → 레지스트리 → 다른 서버에서 pull
```

컨테이너마다 독립된 전체 OS 커널을 설치하는 방식은 아닙니다. macOS/Windows의 Linux 컨테이너는 보통 Docker Desktop이 관리하는 Linux 가상 환경에서 실행됩니다.

[Docker 공식 시작 안내](https://docs.docker.com/get-started/)

## 설치 확인과 첫 실행

Docker Desktop을 설치하고 실행한 뒤 터미널에서 확인합니다. Linux에서는 Docker Engine과 Compose 플러그인 구성을 사용할 수도 있습니다.

```bash
docker version
docker compose version
docker run --rm hello-world
```

| 명령 | 역할 |
|---|---|
| docker version | 클라이언트와 서버 상태 확인 |
| docker compose version | Compose 사용 가능 여부 |
| docker run | 이미지로 새 컨테이너 생성·실행 |
| --rm | 종료 후 컨테이너 자동 제거 |

hello-world 이미지가 없으면 다운로드합니다. Docker CLI가 있어도 엔진이 실행 중이 아니면 컨테이너를 실행할 수 없습니다. 설치 안내: [Docker Desktop](https://docs.docker.com/desktop/)

## 웹 서버 실행과 포트 연결

```bash
docker run -d --name demo-web \
  -p 127.0.0.1:8088:80 nginx:stable
```

브라우저에서 `http://localhost:8088`로 접속합니다.

| 옵션 | 의미 |
|---|---|
| -d | 백그라운드 실행 |
| --name demo-web | 컨테이너 이름 |
| -p 127.0.0.1:8088:80 | 내 PC 8088 → 컨테이너 80, 로컬 접속만 공개 |
| nginx:stable | 이미지 이름:태그 |

```text
브라우저 localhost:8088 → 컨테이너의 Nginx 80
```

`-p 8088:80`처럼 호스트 주소를 생략하면 일반적으로 모든 호스트 인터페이스에 게시됩니다. `EXPOSE 80`만으로 호스트 포트가 열리는 것은 아닙니다.

[공식: 포트 게시](https://docs.docker.com/engine/network/port-publishing/)

## 상태 확인·로그·접속·정리

```bash
docker ps
docker ps -a
docker logs --tail 50 demo-web
docker logs -f demo-web
docker exec -it demo-web sh
```

exec는 실행 중인 컨테이너에 새 명령을 실행합니다. `sh`를 포함하지 않은 이미지도 있습니다. 셸에서 `exit`로 나오고, logs -f는 Ctrl+C로 로그 보기만 끝냅니다.

```bash
docker stop demo-web
docker start demo-web
docker stop demo-web
docker rm demo-web
```

| 명령 | 바꾸는 것 |
|---|---|
| stop | 컨테이너 실행 중지 |
| start | 기존 컨테이너 재시작 |
| rm | 중지한 컨테이너 제거 |
| image ls | 이미지 목록 조회 |
| image rm IMAGE | 지정 이미지 제거 |

다시 run하면 기존 컨테이너를 재시작하는 것이 아니라 새로 만듭니다. 같은 이름이 남아 있으면 이름 충돌이 납니다. 이미지 삭제와 볼륨 삭제는 별개입니다.

## Dockerfile — 각 줄의 역할

| 명령 | 실행 시점·역할 |
|---|---|
| FROM | 빌드 단계의 기반 이미지 |
| WORKDIR | 이후 명령의 작업 폴더 |
| COPY | 빌드 컨텍스트의 파일을 이미지로 복사 |
| RUN | 이미지 빌드 중 명령 실행 |
| ENV | 실행 환경변수 기본값 |
| EXPOSE | 앱이 사용하는 포트 정보 |
| USER | 이후 실행 사용자 |
| ENTRYPOINT | 컨테이너 시작 시 실행할 명령 |

**RUN은 빌드 중, ENTRYPOINT는 컨테이너 실행 때** 사용합니다. COPY는 내 PC의 모든 파일이 아니라 빌드 컨텍스트 안의 파일을 대상으로 합니다. 다음 예제에서는 프로젝트 루트에서 `docker build ... .`을 실행합니다.

[공식: 멀티 스테이지 빌드](https://docs.docker.com/build/building/multi-stage/)

## Spring 프로젝트용 Dockerfile

**기준:** 현재 학습 프로젝트의 Java 21, Maven Wrapper, JAR 이름 `todo-learning-0.0.1-SNAPSHOT.jar`. 프로젝트 루트의 Dockerfile로 사용할 예시입니다.

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /workspace
COPY .mvn .mvn
COPY mvnw pom.xml ./
COPY src src
RUN chmod +x mvnw && ./mvnw -B -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app app \
    && mkdir -p /app/data && chown app:app /app/data
COPY --from=build /workspace/target/todo-learning-0.0.1-SNAPSHOT.jar app.jar
ENV SERVER_ADDRESS=0.0.0.0
ENV SPRING_H2_CONSOLE_ENABLED=false
EXPOSE 8080
USER app
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

| 단계 | 이유 |
|---|---|
| build 단계 | 소스를 컴파일해 JAR 생성 |
| 실행 단계 | JRE와 실행 JAR만 포함 |
| USER app | 앱을 별도 일반 사용자로 실행 |
| /app/data | 현재 H2 파일 DB 저장 위치 |
| SERVER_ADDRESS | 컨테이너 외부에서 전달된 요청을 받도록 설정 |

Docker 빌드에서는 테스트를 건너뛰므로 **별도로 `./mvnw test`를 통과한 뒤** 이미지를 빌드하세요. 빌드에는 기반 이미지·Maven 의존성 다운로드가 필요합니다. image 태그는 변경될 수 있으므로 재현성이 중요한 배포는 검증한 digest로 고정합니다.

기존 로컬 설정 127.0.0.1을 환경변수로 덮어쓰되 호스트 포트는 다음 단계에서 localhost에만 연결합니다. H2 콘솔은 컨테이너에서 비활성화했습니다. JAR 이름을 바꾸면 COPY도 수정해야 합니다.

## .dockerignore와 build·run

프로젝트 루트에 `.dockerignore`를 작성합니다.

```text
.git
target
node_modules
data
.env
.env.*
*.pem
.idea
```

.gitignore와 .dockerignore는 다른 기능입니다. 전자는 Git 추적 제외, 후자는 Docker 빌드 컨텍스트 제외입니다. Maven Wrapper에 필요한 `.mvn`은 제외하지 않습니다.

```bash
./mvnw test
docker build -t todo-learning:1.0 .
docker run -d --name todo-app \
  -p 127.0.0.1:8080:8080 \
  --mount source=todo-data,target=/app/data \
  todo-learning:1.0

docker logs -f todo-app
```

서버 시작 로그를 확인한 뒤 `http://localhost:8080/todos`로 접속합니다. 로컬 Spring이 이미 8080을 사용하면 호스트 쪽만 `127.0.0.1:8081:8080`으로 바꾸세요.

코드를 수정한 뒤에는 새 이미지를 build하고 기존 컨테이너를 stop·rm한 뒤 새 컨테이너를 run합니다. 이미지 빌드만으로 실행 중인 컨테이너가 바뀌지는 않습니다.

## Volume·Bind mount — 데이터 유지

| 방식 | 역할 | 주 용도 |
|---|---|---|
| Named volume | Docker가 관리하는 저장 공간 | DB 파일 |
| Bind mount | 호스트 폴더를 컨테이너 경로에 연결 | 개발 소스·설정 공유 |
| 컨테이너 쓰기 계층 | 컨테이너 자체의 변경 파일 | 삭제해도 되는 임시 파일 |

```bash
docker volume ls
docker volume inspect todo-data
```

앞 단계의 `/app/data`는 named volume으로 연결되어 컨테이너를 삭제해도 데이터가 유지됩니다. 처음 만드는 빈 볼륨과 기존 볼륨의 파일 소유권은 다를 수 있습니다. 권한 오류가 나면 앱 사용자와 볼륨 파일 소유권을 확인하세요.

H2 파일 DB 하나를 여러 앱 컨테이너가 동시에 공유하는 구조로 확장하지 않습니다. 서버 여러 개로 운영하려면 별도의 DB 서버를 사용하세요.

[공식: Volumes](https://docs.docker.com/engine/storage/volumes/)

## Compose — 실행 설정을 파일로

프로젝트 루트에 `compose.yaml`을 작성합니다. 앞의 Dockerfile이 같은 폴더에 있다고 가정합니다.

```yaml
services:
  app:
    build: .
    image: todo-learning:1.0
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      SERVER_ADDRESS: 0.0.0.0
      SPRING_H2_CONSOLE_ENABLED: "false"
    volumes:
      - todo-data:/app/data
    restart: unless-stopped
volumes:
  todo-data:
```

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs -f app
docker compose down
```

| 명령 | 역할 |
|---|---|
| config | 설정 파싱·병합 결과 확인 |
| up -d --build | 필요 시 빌드하고 서비스 시작 |
| logs -f app | app 서비스 로그 |
| down | 해당 프로젝트의 컨테이너·네트워크 정리 |

down은 위 named volume을 기본적으로 유지합니다. **down -v는 해당 볼륨과 데이터를 삭제할 수 있으므로 초기화가 목적일 때만 사용합니다.** Compose의 볼륨은 보통 프로젝트 이름이 접두사로 붙어 앞의 docker run 볼륨과 별개입니다.

docker run 실습을 먼저 했다면 todo-app을 중지해 호스트 포트 충돌을 피하세요. restart 설정은 오류 원인을 해결하거나 앱의 건강 상태를 자동 보장하는 기능이 아닙니다.

[공식: Compose 서비스 설정](https://docs.docker.com/reference/compose-file/services/)

## 컨테이너끼리 연결하는 주소

```text
내 PC → localhost:게시포트 → app 컨테이너
app 컨테이너 → db:5432 → db 컨테이너
```

같은 Compose 네트워크의 서비스들은 서비스 이름으로 서로 찾습니다. app 안의 localhost는 **app 컨테이너 자신**이므로 별도 DB 컨테이너의 주소가 아닙니다.

| 설정 예 | 의미 |
|---|---|
| jdbc:postgresql://db:5432/todos | 같은 네트워크의 db 서비스 |
| ports: 127.0.0.1:8080:8080 | 내 PC에서 앱에 접근 |
| environment | 앱에 전달할 환경변수 |

PostgreSQL로 전환할 때는 주소만 바꾸지 말고 JDBC 드라이버, 계정, 스키마 설정, 준비 완료 확인도 구성합니다. `depends_on`의 단순 시작 순서는 DB 준비 완료를 보장하지 않습니다. healthcheck와 `condition: service_healthy` 또는 앱 재시도 전략이 필요합니다. 위 H2 예제에는 별도 db 서비스가 없습니다.

[공식: Compose 모델](https://docs.docker.com/compose/intro/compose-application-model/)

## 이미지 공유 — login·tag·push·pull

Docker Hub 계정과 본인 네임스페이스의 이미지 저장소가 준비되어 있다고 가정합니다. `MY_DOCKER_ID`를 실제 Docker Hub 계정명으로 바꿉니다.

```bash
docker login
docker tag todo-learning:1.0 MY_DOCKER_ID/todo-learning:1.0
docker push MY_DOCKER_ID/todo-learning:1.0
```

다른 환경에서:

```bash
docker pull MY_DOCKER_ID/todo-learning:1.0
```

| 명령 | 역할 |
|---|---|
| login | 레지스트리 인증 |
| tag | 같은 이미지에 새 이름·태그 부여 |
| push | 레지스트리에 업로드 |
| pull | 레지스트리에서 다운로드 |

push는 이미지 공개 범위와 저장소 권한을 확인한 뒤 실행합니다. 비밀번호·토큰을 Dockerfile의 COPY·ENV로 굽지 않습니다. Apple Silicon과 x86 서버는 CPU 아키텍처가 다를 수 있어 대상 플랫폼을 확인해야 합니다. pull만으로 컨테이너가 실행되지는 않습니다.

[공식: 이미지 빌드·태그·배포](https://docs.docker.com/get-started/docker-concepts/building-images/build-tag-and-publish-an-image/)

## 예제 파일 다운로드

아래 파일을 **Spring 프로젝트 루트**에 복사합니다. 이 자료 폴더 안에는 Spring 소스가 없으므로 여기에서 바로 빌드하지 않습니다.

| 파일 | 프로젝트에서 저장할 이름 |
|---|---|
| [Dockerfile](sample-files/Dockerfile) | Dockerfile |
| [Compose 설정](sample-files/compose.yaml) | compose.yaml |
| [빌드 제외 목록](sample-files/dockerignore.txt) | .dockerignore |

프로젝트의 pom.xml, mvnw, .mvn, src와 같은 위치에 두고 본문의 build/run 또는 Compose 단계를 따르세요. 두 실행 방식을 같은 포트로 동시에 실행하지 않습니다.

## 오류 해결과 GitHub 연결 흐름

| 증상 | 확인할 것 |
|---|---|
| Cannot connect to Docker daemon | Desktop/Engine 실행 여부 |
| port is already allocated | 호스트 포트 점유, 기존 컨테이너 |
| name is already in use | ps -a로 같은 이름 확인 |
| 컨테이너가 곧바로 종료 | logs, 시작 명령, 앱 설정 |
| 브라우저 접속 실패 | 포트 연결·앱 바인딩·기동 로그 |
| Permission denied on /app/data | 볼륨 권한과 실행 사용자 |
| no matching manifest / exec format | 이미지의 OS·CPU 플랫폼 |

```text
코드 작성 → Git 커밋 → GitHub push → 테스트(CI)
  → Docker build → 레지스트리 push → 서버에서 이미지 실행
```

GitHub push와 Docker push는 서로 다른 저장소로 다른 대상을 보냅니다. GitHub Actions로 두 과정을 자동화할 수 있지만 이미지 게시·운영 배포에는 별도의 권한과 설정이 필요합니다.

**예제 검증 범위:** 문서·링크와 Compose 설정을 확인하는 학습 자료입니다. 컨테이너 이미지 빌드·실행이나 레지스트리 게시는 이 작업에서 수행하지 않습니다.
