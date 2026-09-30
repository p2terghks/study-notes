> 이 문서는 원래 Spring 예제 프로젝트의 실행 안내입니다. 이 사이트에는 설명과 코드 발췌가 포함되어 있습니다.

# 처음 배우는 Spring 웹 개발

할 일 관리 웹을 직접 실행하고, 화면 → 컨트롤러 → 서비스 → JPA → DB 흐름을 배우는 예제입니다.

## 실행

Java 21 이상이 필요합니다. 이 프로젝트는 Spring Boot 4.1.1과 Maven을 사용합니다. Maven은 별도로 설치하지 않아도 `mvnw`가 내려받습니다. 첫 실행에는 인터넷이 필요합니다.

프로젝트 폴더의 터미널에서 실행하세요.

```sh
./mvnw spring-boot:run
```

Windows에서는 `mvnw.cmd spring-boot:run`을 사용합니다.

브라우저: <http://localhost:8080/todos>

종료: 실행한 터미널에서 `Ctrl+C`

## 따라 해보기

1. 새 할 일 등록 → `스프링 배우기` 입력 → 저장
2. 목록에 나타나는지 확인
3. 수정 → 제목 변경, 완료 체크 → 수정 저장
4. 삭제 → 목록에서 없어지는지 확인
5. 등록 화면에 공백만 입력 → 오류 메시지 확인
6. <http://localhost:8080/todos/999999/edit> → 없는 할 일의 404 확인
7. 서버를 종료하고 다시 실행 → 삭제하지 않은 데이터가 유지되는지 확인

## DB 들여다보기

<http://localhost:8080/h2-console>에서 아래 값으로 연결합니다.

- Driver Class: `org.h2.Driver`
- JDBC URL: `jdbc:h2:file:./data/todos` (화면의 기본값 대신 이 값을 입력)
- User Name: `sa`
- Password: 비워 두기

```sql
SELECT * FROM TODO;
```

DB 파일은 실행 위치의 `data/`에 저장됩니다. 같은 프로젝트 폴더에서 실행해야 같은 DB를 봅니다.

## 검증

```sh
./mvnw test
```

테스트는 별도 메모리 DB에서 실행됩니다. 웹 요청을 보내 CRUD, 입력 검증, 404, HTML 이스케이프를 확인합니다.

## 예제 범위

개인 PC에서 사용하는 학습용 웹입니다. 로그인과 사용자별 권한은 구현하지 않았습니다. `server.address=127.0.0.1`로 로컬 접속만 허용합니다. 외부 공개 전에 Spring Security 인증·인가·CSRF 보호, 운영 DB와 비밀번호 설정, DB 마이그레이션을 추가해야 합니다.

## 실행 문제 해결

- `Permission denied`: `chmod +x mvnw` 후 다시 실행
- Java 관련 오류: `java -version`과 IDE의 프로젝트 JDK가 21 이상인지 확인
- 8080 포트 사용 중: `./mvnw spring-boot:run -Dspring-boot.run.arguments=--server.port=8081` 후 8081로 접속
- DB가 사용 중이라는 오류: 같은 프로젝트의 서버를 두 번 실행했는지 확인
- 다운로드 실패: 인터넷 연결과 Maven 저장소 접근 여부 확인

