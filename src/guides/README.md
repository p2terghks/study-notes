# Kubernetes · Terraform 강의 문서 생성

`kubernetes-terraform-guide.md`는 편집용 원문입니다. `INCLUDE` 지시문은 배포용 예제 파일을 읽어 코드 블록으로 삽입하므로 설명 문서와 다운로드 코드가 일치합니다.

저장소 루트에서 Python 가상환경을 만든 후 아래를 실행합니다.

```sh
python -m pip install -r src/guides/requirements.txt
python src/guides/build_kubernetes_terraform.py
```

생성물은 `docs/quick-reference/kubernetes-terraform-guide.html`, 같은 이름의 Markdown, `kubernetes-terraform-examples.zip`입니다. 기존 `catalog.json`과 루트 `index.html`의 목록도 동기화합니다. 페이지는 외부 CDN 없이 동작합니다.

검증 범위 문구는 생성 스크립트의 report 변수에 있습니다. 실습의 실제 검증 범위가 달라졌다면 근거에 맞게 수정하세요. ZIP에는 state, plan, `.terraform` 다운로드 디렉터리를 넣지 않습니다.
