# React를 먼저 빌드하고 생성된 정적 파일을 Spring JAR에 포함한다.
FROM --platform=$BUILDPLATFORM node:22-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm test && npm run build

# Java 바이트코드는 이식 가능하므로 빌드는 호스트 아키텍처에서 실행해 에뮬레이션 비용을 줄인다.
FROM --platform=$BUILDPLATFORM maven:3.9.11-eclipse-temurin-17 AS build
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates python3 && rm -rf /var/lib/apt/lists/*
# RDS TLS 연결에서 서버 인증서와 호스트명을 검증할 공개 CA 묶음.
RUN mkdir /certs && curl --fail --show-error --location https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o /certs/global-bundle.pem
WORKDIR /build
COPY pom.xml ./
COPY src ./src
COPY --from=frontend /build/src/main/resources/static ./src/main/resources/static
RUN --mount=type=cache,target=/root/.m2 mvn -B -q verify

# 실행 이미지에는 JRE와 결과물만 포함하고 비루트 계정으로 실행한다.
FROM eclipse-temurin:17-jre-jammy
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 10001 campus && useradd --uid 10001 --gid campus --no-create-home campus
WORKDIR /app
COPY --from=build --chown=campus:campus /build/target/campus-1.0.0.jar /app/app.jar
COPY --from=build --chown=campus:campus /certs/global-bundle.pem /app/certs/global-bundle.pem
USER campus
EXPOSE 8080
ENV SPRING_PROFILES_ACTIVE=prod
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=70", "-jar", "/app/app.jar"]
