# GitHub · Git 사용법 요약

## Git과 GitHub부터 구분하기

**Git은 변경 이력을 관리하는 도구, GitHub는 저장소를 공유하고 협업하는 서비스입니다.** 터미널의 git 명령은 주로 Git 기능이고, gh 명령은 별도 설치하는 GitHub CLI입니다.

| 용어 | 쉽게 설명하면 |
|---|---|
| Repository | 파일과 변경 이력을 담은 저장소 |
| Commit | 변경 내용을 기록한 하나의 이력 |
| Branch | 다른 작업과 분리한 개발 흐름 |
| Remote | 연결된 원격 저장소 |
| origin | 자주 쓰는 원격 저장소 별칭, 고정된 특별 서버가 아님 |
| Pull Request(PR) | 변경 사항의 검토·병합 요청 |
| Fork | 다른 GitHub 저장소를 내 소유로 복제 |

```text
파일 수정 → git add → git commit → git push → GitHub
            준비 영역    로컬 기록     원격 전송
```

이 문서는 학습용 명령 예시입니다. 실제 저장소 생성·게시·PR 작성은 수행하지 않았습니다. `OWNER`, `REPO`는 본인의 계정·저장소 이름으로 바꿔 실행하세요.

[GitHub 공식: Git 소개](https://docs.github.com/en/get-started/using-git/about-git)

## 설치 확인·사용자 정보·로그인

```bash
git --version
gh --version

git config --global user.name "내 이름"
git config --global user.email "내 GitHub 커밋 이메일"

gh auth login
gh auth status
```

| 명령 | 역할 |
|---|---|
| git config | Git 설정 변경 |
| --global | 현재 OS 사용자의 기본 설정 |
| user.name / user.email | 커밋 작성자 정보, 로그인 정보가 아님 |
| gh auth login | 브라우저 등으로 GitHub 인증 |
| gh auth status | 인증 상태 확인 |

`gh`가 없다면 [GitHub CLI 설치 안내](https://cli.github.com/)를 따릅니다. 로그인에서 HTTPS를 선택하고 Git 인증도 설정하면 push/pull에 사용할 수 있습니다. SSH 방식도 가능합니다.

GitHub 계정 비밀번호를 HTTPS Git 비밀번호로 쓰지 않습니다. 인증 도구·토큰·SSH를 사용하고 토큰을 소스나 원격 URL에 넣어 저장하지 마세요. 이메일 공개가 부담되면 GitHub 설정의 noreply 이메일을 사용할 수 있습니다.

[공식: 인증 방식](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github)

## 기존 프로젝트 내려받기 — clone

```bash
git clone https://github.com/OWNER/REPO.git
cd REPO
git status
git remote -v
```

**clone:** 파일뿐 아니라 Git 이력도 내려받고 origin을 연결합니다. 이미 clone한 프로젝트에 다시 git init을 할 필요는 없습니다.

| 확인 명령 | 볼 내용 |
|---|---|
| git status | 현재 브랜치, 변경 파일 |
| git remote -v | 원격 저장소 주소 |
| git branch | 로컬 브랜치 |
| git log --oneline -5 | 최근 커밋 5개 |

GitHub의 Download ZIP은 파일을 받는 방식이고 일반적으로 Git 이력과 원격 연결이 포함되지 않습니다. 다른 사람의 저장소를 clone했다고 push 권한이 생기지는 않습니다.

## 내 프로젝트 처음 올리기 — init

**전제:** 아직 Git 저장소가 아닌 프로젝트 폴더에서 실행합니다. GitHub에서는 README·라이선스를 자동 생성하지 않은 빈 저장소를 먼저 만듭니다.

```bash
git init -b main
git status
```

`.gitignore`를 먼저 작성하고 제외 대상을 확인한 뒤 실행합니다.

```bash
git add .
git diff --cached
git commit -m "Initial project"
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main
```

| 명령 | 의미 |
|---|---|
| init -b main | main을 초기 브랜치로 저장소 생성 |
| add . | 현재 폴더 아래 변경을 준비 영역에 추가 |
| diff --cached | 커밋에 들어갈 변경 확인 |
| remote add origin | 원격 저장소 연결 |
| push -u origin main | 원격에 전송하고 추적 관계 설정 |

GitHub에도 이미 커밋이 있다면 위 빈 저장소 절차 대신 clone한 폴더에 필요한 파일을 옮겨 커밋하는 방법이 초보자에게 명확합니다. origin이 이미 있다면 먼저 remote -v로 주소를 확인하세요.

## 저장·비교·이력 — 매일 쓰는 명령

```bash
git status
git diff

git add src/main/java/com/example/todolearning/todo/TodoController.java
git diff --cached
git commit -m "Add todo validation"
git push
```

파일 경로는 현재 Spring 예제 기준입니다. 다른 저장소에서는 실제 경로로 바꿉니다.

| 명령 | 비교·작업 대상 |
|---|---|
| git diff | 작업 파일과 준비 영역 |
| git diff --cached | 준비 영역과 마지막 커밋 |
| git diff HEAD | 추적 파일의 현재 상태와 마지막 커밋 |
| git log --oneline --graph -10 | 최근 이력 구조 |
| git show HEAD | 마지막 커밋의 내용 |

**commit은 로컬 기록, push는 원격 전송입니다.** Git이 아직 추적하지 않는 새 파일은 일반 diff에 내용이 나오지 않으므로 status도 확인합니다. add 후 다시 수정했다면 그 수정까지 커밋하려면 다시 add해야 합니다.

## 브랜치와 최신 변경 가져오기

```bash
git switch main
git pull --ff-only
git switch -c feature/todo-search
```

수정·테스트·커밋 후:

```bash
git push -u origin feature/todo-search
```

| 명령 | 역할 |
|---|---|
| switch main | main으로 이동 |
| switch -c 이름 | 새 브랜치 생성 후 이동 |
| fetch origin | 원격 이력 갱신, 현재 브랜치를 자동 병합하지 않음 |
| pull --ff-only | 원격 변경으로 단순 전진이 가능할 때만 반영 |

브랜치 이동 전 작업 내용을 커밋하거나 stash로 보관합니다. `pull --ff-only`가 실패하면 로컬·원격에 각자 커밋이 있을 수 있습니다. 무조건 강제 push하지 말고 이력을 확인한 뒤 팀 정책에 따라 merge/rebase를 선택합니다.

```bash
git fetch origin
git log --oneline --graph --all -12
```

## Pull Request — 검토하고 병합하기

**흐름:** 브랜치 push → PR 생성 → 변경 검토·자동 검사 → 병합 → 로컬 main 갱신.

```bash
gh pr create --base main --head feature/todo-search \
  --title "할 일 검색 기능 추가" \
  --body "제목으로 할 일을 검색합니다. 검증: ./mvnw test"

gh pr view --web
gh pr checks
```

위 PR 본문의 검증 문구는 실제 테스트를 통과했을 때 작성합니다. gh 대신 GitHub 웹의 Compare & pull request로 진행해도 됩니다.

| PR 항목 | 적을 내용 |
|---|---|
| 제목 | 무엇이 달라졌는지 |
| 설명 | 문제·해결 내용·동작 변화 |
| 검증 | 실제 실행한 테스트 |
| base / head | 반영 대상 / 변경 브랜치 |

검토와 저장소 규칙을 충족한 뒤 웹에서 병합합니다. 병합 후 로컬 main에서 pull합니다. squash 병합은 커밋 이력이 달라져 `git branch -d`가 병합 여부를 인식하지 못할 수 있으므로 이력을 확인하고 정리하세요.

[GitHub 공식: PR 시작하기](https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart)

## 충돌 해결 — 같은 줄을 바꿨을 때

기능 브랜치에서 최신 main을 병합하는 예시입니다. 먼저 진행 중인 변경을 커밋해 작업 폴더를 정리합니다.

```bash
git fetch origin
git merge origin/main
git status
```

충돌 파일에는 다음 같은 표시가 나타납니다.

```text
<<<<<<< HEAD
현재 브랜치의 내용
=======
병합하는 쪽의 내용
>>>>>>> origin/main
```

1. 양쪽 의도를 확인하고 최종 코드를 직접 작성합니다.
2. 충돌 표시를 모두 제거하고 저장합니다.
3. 테스트 후 해당 파일을 add합니다.
4. merge 커밋을 완성합니다.

```bash
git add path/to/conflicted-file
git commit
git push
```

`path/to/conflicted-file`은 실제 충돌 파일로 바꿉니다. 진행 중인 merge를 취소하려면 `git merge --abort`를 사용합니다. 이것은 이미 완료된 병합을 되돌리는 명령은 아닙니다.

## 되돌리기와 임시 보관

| 목적 | 명령 | 결과 |
|---|---|---|
| add만 취소 | git restore --staged FILE | 파일 수정은 유지 |
| 파일 수정 버리기 | git restore FILE | 추적 파일을 준비 영역 상태로 복원 |
| 커밋 취소 이력 남기기 | git revert COMMIT | 반대 변경을 새 커밋으로 생성 |
| 수정 임시 보관 | git stash push -u -m "작업 중" | 미추적 파일도 포함, ignored 파일은 제외 |
| 보관 목록 | git stash list | stash 확인 |
| 복원 후 보관도 유지 | git stash apply | 복원, 충돌 가능 |

FILE과 COMMIT은 실제 파일 경로·커밋 ID로 바꿉니다. `restore FILE`은 커밋되지 않은 수정을 버릴 수 있으므로 먼저 diff를 확인하세요. `revert`는 공유한 이력을 다시 쓰지 않고 취소 기록을 남길 때 적합합니다. 복잡한 merge 커밋 revert는 별도 판단이 필요합니다.

[Git 공식: restore](https://git-scm.com/docs/git-restore)

## .gitignore — 올리지 않을 파일

Spring·React 프로젝트에서 자주 쓰는 예시입니다. 프로젝트 루트에 `.gitignore`로 작성합니다.

```gitignore
# 빌드 결과와 의존성
target/
build/
node_modules/
dist/

# 개인 설정·비밀값·로컬 DB
.idea/
.DS_Store
.env
.env.*
!.env.example
data/
*.pem
```

`.env.example`에는 실제 비밀번호 대신 변수 이름과 예시값만 넣습니다. .gitignore는 이미 추적 중인 파일을 자동으로 제외하거나 과거 커밋에서 지우지 않습니다.

```bash
git check-ignore -v .env
```

이미 비밀키를 올렸다면 파일만 지우는 것으로 끝나지 않습니다. 해당 키를 폐기·교체하고 노출된 이력을 처리해야 합니다. 일반 빌드 파일의 추적 제외는 필요한 파일만 `git rm --cached FILE`로 처리합니다.

## GitHub Actions — push·PR 때 테스트

**기능:** GitHub가 저장소 이벤트에 맞춰 자동 작업을 실행합니다. 아래는 배포가 아닌 Maven 테스트 워크플로입니다.

파일: `.github/workflows/test.yml`

```yaml
name: Java tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-java@v6
        with:
          distribution: temurin
          java-version: '21'
          cache: maven
      - name: Run tests
        run: |
          chmod +x mvnw
          ./mvnw -B test
```

| 항목 | 역할 |
|---|---|
| on | 실행할 이벤트 |
| jobs | 실행할 작업 |
| runs-on | 실행 환경 |
| uses | 준비된 Action 사용 |
| run | 셸 명령 실행 |

루트에 pom.xml, mvnw, .mvn이 있는 Maven 프로젝트 기준입니다. Actions 탭에서 결과를 확인합니다. 메이저 버전 태그는 업데이트될 수 있으며 더 엄격한 고정이 필요하면 검증한 커밋 SHA로 고정합니다.

[checkout 공식](https://github.com/actions/checkout) · [setup-java 공식](https://github.com/actions/setup-java)

## 예제 파일 다운로드

| 파일 | 프로젝트에서 저장할 위치 |
|---|---|
| [Git 제외 목록](sample-files/gitignore.txt) | 프로젝트 루트의 .gitignore |
| [자동 테스트 설정](sample-files/test-workflow.yml) | .github/workflows/test.yml |

이미 파일이 있다면 필요한 항목을 비교해서 합칩니다. 기존 프로젝트 설정을 무조건 덮어쓰지 마세요. 워크플로 파일을 저장소에 커밋하고 push하면 설정한 이벤트에 따라 GitHub에서 실행됩니다.

## 오류별 확인과 전체 흐름

| 증상 | 확인할 것 |
|---|---|
| not a git repository | 저장소 폴더에서 실행했는지 |
| nothing to commit | 파일 저장·현재 위치·add·ignore 여부 |
| Authentication failed | gh auth status, 인증 방식 |
| Permission denied | 저장소 권한·SSH 키·원격 주소 |
| non-fast-forward | 원격에 새 커밋이 있는지 fetch 후 비교 |
| remote origin already exists | remote -v로 기존 주소 확인 |

```text
clone → main 최신화 → 작업 브랜치 → 수정 → 테스트
    → diff → add → commit → push → PR → 검토 → 병합
```

GitHub Issues는 할 일을 기록하고, PR은 실제 변경을 검토하는 곳입니다. Docker 이미지와 Git 저장소는 별개이며 다음 Docker 요약에서 배포용 이미지 흐름을 다룹니다.

## 공부한 내용 기록하기 — 학습 노트와 블로그

**한 주제마다 ‘배운 것 → 코드 → 확인 결과 → 헷갈린 점’을 남기세요.** 매일 길게 쓰기보다 나중에 다시 이해하고 재현할 수 있는 기록이 좋습니다.

| 구분 | GitHub 학습 노트(TIL: Today I Learned) | 블로그 글 |
|---|---|---|
| 목적 | 내가 복습할 기록 | 다른 사람도 이해할 설명 |
| 분량 | 개념 하나와 작은 예제 | 질문 하나를 해결하는 글 |
| 순서 | 핵심 → 코드 → 결과 → 다음 할 일 | 배경 → 개념 → 실습 → 문제 해결 → 정리 |
| 제목 예시 | Spring 컨트롤러와 서비스 역할 정리 | Spring에서 컨트롤러와 서비스를 나누는 이유 |

먼저 짧은 학습 노트를 쓰고, 설명할 수 있게 된 주제를 블로그 글로 확장하세요. 아직 확인하지 않은 내용은 ‘추측’이나 ‘추가 확인’으로 구분합니다.

## Markdown 기본 문법 — .md 파일 작성하기

Markdown은 일반 텍스트에 제목·목록·코드 등의 표시를 붙이는 작성 방식입니다. 파일을 `.md` 확장자로 저장합니다.

````markdown
# 글 제목

## 핵심 개념

**중요한 내용**과 `코드 이름`을 구분합니다.

- 배운 개념 하나
- 헷갈렸던 점 하나

1. 코드를 작성합니다.
2. 실행 결과를 확인합니다.

> 내 말로 정리한 한 줄 요약

```java
System.out.println("Hello, Spring!");
```

[GitHub Markdown 문법](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)

![실행 결과 화면](images/result.png)

- [x] 예제 실행
- [ ] 추가 복습
````

`#`는 글 제목, `##`는 큰 항목, `###`는 하위 항목입니다. 문단·목록·코드 블록 앞뒤에 빈 줄을 넣으세요. 코드 블록에는 `java`, `python`, `bash`처럼 언어를 적습니다. 이미지 예시는 **현재 Markdown 파일 옆의 images 폴더에 result.png를 저장한 경우**입니다. 이미지 파일도 함께 커밋해야 합니다.

GitHub에서 파일을 열거나 에디터의 Markdown 미리보기로 표시를 확인하세요. 블로그 편집기는 Markdown 지원 범위가 다를 수 있으므로 게시 전 미리보기도 확인합니다.

[GitHub 공식: 기본 문법](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) · [공식: 코드 블록](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-and-highlighting-code-blocks)

## 학습 기록 템플릿 — 복사해서 채우기

[학습 기록 템플릿 파일](sample-files/til-template.md)을 복사하거나 아래 틀을 사용하세요. 대괄호 안을 실제 학습 내용으로 바꿉니다. 실행하지 않았다면 결과를 꾸며 쓰지 않고 ‘미실행’으로 남깁니다.

````markdown
# [주제] 학습 기록

- 날짜: YYYY-MM-DD
- 학습 목표: [오늘 설명할 수 있게 되고 싶은 것]
- 환경: [언어·프레임워크 버전, 필요한 실행 조건]

## 핵심 개념

[무엇인지, 언제 쓰는지 내 말로 2~3문장]

## 예제와 확인 결과

```java
// 직접 작성한 최소 예제: 사용한 언어에 맞게 java도 변경
```

- 실행 방법: [실행 명령 또는 화면 조작]
- 예상 결과: [기대하는 동작]
- 실제 결과: [관찰한 동작 또는 미실행]

## 막힌 점과 해결

- 현상: [오류 메시지 또는 재현 조건]
- 원인: [확인한 근거, 모르면 추가 확인]
- 해결: [바꾼 내용과 다시 확인한 결과]

## 복습과 참고 자료

- 한 줄 요약: [가장 중요한 내용]
- 다음에 확인할 것: [남은 질문]
- 참고: [자료 이름과 링크]
````

예를 들어 Spring 요청 흐름을 배웠다면 ‘컨트롤러는 요청을 받고, 서비스는 처리 로직을 수행한다’고 적은 뒤, 이 프로젝트에서 직접 따라간 메서드 이름과 결과를 덧붙이세요. 코드를 붙이는 데서 끝내지 않고 **왜 이 코드가 필요한지** 한 문장으로 설명하는 것이 핵심입니다.

## 블로그 글 작성법 — 질문 하나를 끝까지 설명하기

**독자와 질문을 먼저 정합니다.** 예: ‘Spring 입문자에게 컨트롤러와 서비스의 역할 차이를 설명한다.’

| 순서 | 적을 내용 | 작성 요령 |
|---|---|---|
| 제목 | 어떤 질문을 해결하는지 | ‘Spring 공부’보다 ‘컨트롤러와 서비스는 어떤 역할을 할까?’ |
| 배경 | 왜 궁금했는지, 어떤 문제가 있었는지 | 상황을 2~3문장으로 설명 |
| 개념 | 이해에 필요한 용어와 흐름 | 처음 나오는 용어는 짧게 풀이 |
| 실습 | 환경, 핵심 코드, 실행 방법과 결과 | 코드는 필요한 부분만, 전체 코드는 저장소 링크 |
| 문제 해결 | 증상 → 원인 → 수정 → 재확인 | 직접 겪은 경우만 작성 |
| 정리 | 배운 점, 한계, 남은 질문 | 본문에서 확인한 내용으로 마무리 |
| 참고 | 공식 문서·강의·참고 글 | 인용과 내 설명을 구분하고 출처 표기 |

[블로그 템플릿 파일](sample-files/blog-template.md)을 복사해 채우면 됩니다. 학습 기록에서 핵심 개념과 예제를 가져오고, 처음 읽는 사람에게 필요한 배경 설명을 추가하세요. 오류 해결 글은 ‘이 설정으로 해결됐다’뿐 아니라 적용 조건도 적습니다.

작성 예시 흐름: **‘할 일 저장 요청은 어디로 갈까?’ → 요청 처리 흐름 설명 → 관련 코드 발췌 → 직접 실행한 결과 → 역할을 나누며 이해한 점.**

## 학습 파일 정리와 커밋 순서

학습 저장소를 따로 만든다면 다음처럼 시작할 수 있습니다. 아래는 제안 구조이며 폴더·파일을 실제로 만든 뒤 명령을 실행합니다.

```text
study-notes/
├── README.md
└── til/
    ├── spring/
    │   ├── 2026-09-29-controller-service.md
    │   └── images/
    │       └── result.png
    ├── react/
    └── git/
```

루트 README에는 `[컨트롤러와 서비스](til/spring/2026-09-29-controller-service.md)`처럼 학습 목록을 연결합니다. 파일 이름은 날짜와 주제를 일관되게 사용하면 찾기 쉽습니다.

**전제:** Git 저장소와 origin 연결이 되어 있어야 합니다. 처음이라면 앞의 ‘내 프로젝트 처음 올리기’ 절차를 먼저 확인하세요. 다음 명령은 위 구조의 `study-notes` 루트에서 실행하는 예시입니다.

```bash
git status
git add README.md til/spring/2026-09-29-controller-service.md
# 이미지를 추가했다면 해당 파일도 준비 영역에 추가
# git add til/spring/images/result.png
git diff --cached
git commit -m "docs: Spring 컨트롤러와 서비스 학습 정리"
git push
```

첫 push이고 원격 추적이 설정되지 않았다면 현재 브랜치를 확인하고 `git push -u origin 브랜치이름`을 사용합니다. `docs:`는 문서 변경을 나타내는 흔한 작성 관례이며 Git의 필수 문법은 아닙니다. 복습하며 고쳤다면 `docs: 서비스 역할 설명과 예제 보완`처럼 변경 내용을 적습니다.

**한 주제의 의미 있는 변경을 한 커밋으로 묶으세요.** GitHub에 Markdown을 push하면 저장소에서 읽을 수 있습니다. 별도 블로그에 공개하려면 해당 블로그 편집기에 옮겨 게시하거나 별도의 사이트 게시 설정이 필요합니다.

## 게시 전 확인 — 1분 점검

- 제목만 보고 어떤 내용을 배웠는지 알 수 있는가?
- 개념을 내 말로 설명하고 코드의 이유를 적었는가?
- 실행 환경·방법·실제 결과를 적었는가?
- 코드, 링크, 이미지가 미리보기에서 제대로 보이는가?
- 해결한 사실과 아직 확인하지 못한 내용을 구분했는가?
- 참고한 문서·강의·이미지의 출처를 적었는가?
- 코드나 화면 캡처에 비밀번호·토큰·개인정보가 없는가?

처음에는 **개념 3줄 + 작은 코드 하나 + 결과 + 남은 질문 하나**로 시작해도 충분합니다.
