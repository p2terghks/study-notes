#!/usr/bin/env python3
"""Build the lecture document. Requires markdown and beautifulsoup4."""
from pathlib import Path
import re, json, hashlib, html, zipfile
import markdown
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parents[2]
dest = root / 'docs/quick-reference'
examples = dest / 'sample-files/kubernetes-terraform'
source = (Path(__file__).parent / 'kubernetes-terraform-guide.md').read_text()
def include(m):
    path, language = m.groups()
    return '\n```' + language + '\n' + (examples / path).read_text().rstrip() + '\n```\n'
source = re.sub(r'<!-- INCLUDE:([^:]+):([^ ]+) -->', include, source)
report = '''검증 완료: Terraform 1.16.5에서 두 예제의 `fmt -check`와 `validate`를 통과했습니다. 기초 실습은 실제 plan·apply, 재실행 시 변경 없음, replicas 변경, 잘못된 입력 거부, destroy까지 확인했습니다. Kubernetes provider 2.38.0을 사용했으며 macOS ARM64·Linux AMD64·Windows AMD64의 체크섬을 잠금 파일에 기록했습니다.

Kubernetes YAML의 구조와 label·selector·포트·ConfigMap 참조를 검사했습니다. 로컬 Docker 데몬 연결이 유지되지 않아 Kubernetes 클러스터에서의 실제 배포·접속과 Terraform Kubernetes plan/apply는 실행 검증하지 못했습니다. 따라서 해당 단계의 화면과 동작 설명은 예상 결과입니다. HTML의 목차·문서 내부 링크·예제 다운로드 경로와 데스크톱/모바일 배치, 검색, 테마 전환, 복습 문제 펼치기를 확인했습니다. 실제 AWS 자원은 만들지 않았습니다.'''
source = source.replace('<!-- VALIDATION_REPORT -->', report)
(dest / 'kubernetes-terraform-guide.md').write_text(source)
rendered = markdown.markdown(source, extensions=['fenced_code', 'tables', 'toc', 'sane_lists'])
soup = BeautifulSoup(rendered, 'html.parser')
soup.h1.decompose()
links=[]
for i,h in enumerate(soup.find_all('h2'),1):
    h['id']=f'chapter-{i}'
    links.append(f'<a href="#chapter-{i}">{html.escape(h.get_text())}</a>')
for table in soup.find_all('table'):
    wrapper=soup.new_tag('div',attrs={'class':'table-scroll','tabindex':'0','aria-label':'가로 스크롤 가능한 표'})
    table.wrap(wrapper)
for pre in soup.find_all('pre'):
    wrapper=soup.new_tag('div',attrs={'class':'codebox'})
    pre.wrap(wrapper)
    button=soup.new_tag('button',attrs={'class':'copy','type':'button','aria-label':'이 코드 복사'})
    button.string='복사'
    wrapper.insert(0,button)
css='''
:root{color-scheme:light;--bg:#fff;--panel:#f7f8fa;--ink:#202b39;--muted:#536477;--line:#dce3eb;--accent:#205b8c;--code:#f3f5f8}
:root[data-theme=dark]{color-scheme:dark;--bg:#121820;--panel:#1b2430;--ink:#e7edf5;--muted:#adbacb;--line:#354456;--accent:#8cc8f6;--code:#1b2430}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:32px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.95 -apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR',sans-serif}a{color:var(--accent);text-underline-offset:4px}button,input{font:inherit}button{cursor:pointer}aside{position:fixed;inset:0 auto 0 0;width:300px;padding:26px 23px;background:var(--panel);border-right:1px solid var(--line);overflow-y:auto}aside .brand{font-size:12px;letter-spacing:.12em;color:var(--muted);margin:20px 0}aside input{width:100%;min-width:0;padding:9px 11px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);font-size:13px}aside label{display:block;font-size:12px;color:var(--muted)}#count{font-size:12px;color:var(--muted)}nav a{display:block;text-decoration:none;color:var(--ink);font-size:13px;line-height:1.65;padding:9px 0;border-bottom:1px solid var(--line)}nav a:hover{color:var(--accent)}main{margin-left:300px;max-width:1220px;padding:64px 58px 100px;min-width:0}header{border-bottom:2px solid var(--ink);padding-bottom:35px;margin-bottom:32px}.eyebrow{font-size:12px;letter-spacing:.13em;color:var(--accent)}h1{font-size:clamp(30px,4vw,48px);line-height:1.35;letter-spacing:-.05em;margin:20px 0}header p{color:var(--muted)}h2{word-break:keep-all;overflow-wrap:anywhere;font-size:25px;line-height:1.55;letter-spacing:-.03em;margin:65px 0 22px;padding-bottom:13px;border-bottom:2px solid var(--line)}p{margin:16px 0;overflow-wrap:anywhere}li{margin:9px 0;overflow-wrap:anywhere}ul,ol{padding-left:25px}.actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:24px}.actions a,.actions button{font-size:13px;text-decoration:none;padding:8px 13px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--accent)}.flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;align-items:stretch;gap:10px;margin:25px 0;padding:18px;border:1px solid var(--line);border-radius:8px}.flow div{background:var(--panel);padding:14px;border-radius:5px;line-height:1.6}.flow strong,.flow small{display:block}.flow small{font-size:12px;color:var(--muted);margin-top:6px}.flow span{align-self:center;color:var(--muted)}table{border-collapse:collapse;min-width:540px;width:100%;font-size:14px;line-height:1.8}th,td{border-bottom:1px solid var(--line);padding:12px 13px;text-align:left;vertical-align:top}th{background:var(--panel)}.table-scroll{overflow-x:auto;margin:22px 0}code{font: .87em/1.7 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--code);border-radius:3px;padding:2px 4px;overflow-wrap:anywhere}.codebox{position:relative;margin:23px 0;background:var(--code);border:1px solid var(--line);border-radius:8px;overflow:hidden}pre{margin:0;padding:48px 20px 22px;white-space:pre;overflow-x:auto;font-size:13px;line-height:1.8}pre code{padding:0;font-size:inherit;background:transparent;overflow-wrap:normal}.copy{position:absolute;top:8px;right:10px;background:var(--bg);border:1px solid var(--line);color:var(--muted);border-radius:5px;font-size:12px;padding:3px 11px}details{border:1px solid var(--line);border-radius:7px;margin:13px 0;padding:15px 18px}summary{cursor:pointer;font-weight:600;line-height:1.7}footer{margin-top:55px;padding-top:20px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}#copy-status{position:fixed;bottom:20px;right:20px;background:var(--ink);color:var(--bg);padding:6px 14px;border-radius:7px;font-size:13px}#copy-status:empty{display:none}[hidden]{display:none!important}:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media(max-width:1050px){aside{width:260px}main{margin-left:260px;padding:44px 30px 80px}}
@media(max-width:760px){aside{position:relative;width:100%;max-height:none;padding:22px;border-right:0;border-bottom:1px solid var(--line)}aside nav{max-height:220px;overflow:auto}main{margin:0;padding:30px 21px 65px}h2{font-size:22px;margin-top:48px}.flow{grid-template-columns:1fr;padding:12px}.flow span{text-align:center;transform:rotate(90deg)}pre{font-size:12px}header{padding-bottom:26px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{html{color-scheme:light!important;--bg:#fff!important;--ink:#111!important;--muted:#444!important;--panel:#f5f5f5!important;--line:#bbb!important;--accent:#111!important;--code:#f5f5f5!important}aside,.actions,.copy,#copy-status{display:none!important}main{margin:0;max-width:none;padding:0;font-size:10pt}h1{font-size:28pt}h2{font-size:17pt;break-before:page}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:8pt;padding:12px}table{min-width:0;font-size:8pt}.table-scroll{overflow:visible}tr{break-inside:avoid}a{color:#111;text-decoration:none}.flow{break-inside:avoid}details{break-inside:avoid} @page{size:A4;margin:16mm}}
'''
script='''
const input=document.querySelector('#search');const links=[...document.querySelectorAll('nav a')];
function filter(){const terms=input.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);let count=0;for(const a of links){const target=document.querySelector(a.getAttribute('href'));let text=target.textContent;let n=target.nextElementSibling;while(n&&n.tagName!=='H2'){text+=' '+n.textContent;n=n.nextElementSibling}const show=terms.every(t=>text.toLowerCase().includes(t));a.hidden=!show;if(show)count++}document.querySelector('#count').textContent=count+'개 주제 / 전체 '+links.length+'개'}input.addEventListener('input',filter);filter();
const theme=document.querySelector('#theme');function updateTheme(){const dark=document.documentElement.dataset.theme==='dark';theme.textContent=dark?'라이트 모드':'다크 모드';theme.setAttribute('aria-pressed',String(dark))}theme.addEventListener('click',()=>{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;try{localStorage.setItem('study-notes-theme',next)}catch{}updateTheme()});updateTheme();
document.querySelector('#print').addEventListener('click',()=>window.print());
let opened=[];window.addEventListener('beforeprint',()=>{opened=[...document.querySelectorAll('details')].filter(x=>!x.open);opened.forEach(x=>x.open=true)});window.addEventListener('afterprint',()=>opened.forEach(x=>x.open=false));
document.addEventListener('click',async e=>{const b=e.target.closest('.copy');if(!b)return;const status=document.querySelector('#copy-status');try{await navigator.clipboard.writeText(b.parentElement.querySelector('code').textContent);status.textContent='코드를 복사했습니다.'}catch{status.textContent='복사가 제한되었습니다. 코드를 직접 선택해 주세요.'}setTimeout(()=>status.textContent='',2500)});
'''
page='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="쿠버네티스와 테라폼을 처음 배우는 사람을 위한 36개 주제의 상세 강의 노트. 개념, 코드 해설, 실습, 오류 해결과 복습 문제."><title>쿠버네티스 · 테라폼 | 기초부터 실습까지</title><script>try{document.documentElement.dataset.theme=localStorage.getItem('study-notes-theme')||'light'}catch{}</script><style>'''+css+'''</style></head><body><aside><a href="../../index.html">← 학습 요약 전체 목록</a><p class="brand">KUBERNETES / TERRAFORM</p><label for="search">목차·본문 검색</label><input id="search" type="search" placeholder="Pod, 상태 파일, 오류 해결…"><p id="count" aria-live="polite"></p><nav aria-label="강의 목차">'''+''.join(links)+'''</nav></aside><main><header><div class="eyebrow">LECTURE NOTES · 2026.10.16</div><h1>쿠버네티스 · 테라폼<br>기초부터 실습까지</h1><p>36개 주제 · 개념과 비유 · 코드 한 줄씩 풀이 · 로컬 실습 3개 · 오류 해결 · 복습 문제</p><div class="actions"><a href="#chapter-1">처음부터 읽기</a><a href="#chapter-16">실습 시작</a><a href="kubernetes-terraform-examples.zip" download>예제 ZIP</a><a href="kubernetes-terraform-guide.md" download>Markdown 원문</a><button type="button" id="theme" aria-pressed="false">다크 모드</button><button type="button" id="print">인쇄 · PDF 저장</button></div></header><div class="flow" role="img" aria-label="Terraform이 실행 기반을 준비하고 Kubernetes가 원하는 상태를 유지하며 Pod에서 앱이 실행됩니다"><div><strong>Terraform</strong><small>자원 구성 작성·계획·적용</small></div><span>→</span><div><strong>Kubernetes</strong><small>배치·복제·교체·상태 조정</small></div><span>→</span><div><strong>Pod / 앱</strong><small>사용자 요청을 실제로 처리</small></div></div><article>'''+str(soup)+'''</article><footer>공식 문서 기반의 독립 학습 자료 · 실제 강의 영상의 요약본은 아닙니다. <a href="../../index.html">전체 학습 목록으로</a></footer></main><div id="copy-status" role="status" aria-live="polite"></div><script>'''+script+'''</script></body></html>'''
(dest/'kubernetes-terraform-guide.html').write_text(page)
with zipfile.ZipFile(dest/'kubernetes-terraform-examples.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(examples.rglob('*')):
        if not p.is_file() or '.terraform' in p.parts or '.tfstate' in p.name or p.suffix=='.tfplan':continue
        z.write(p,Path('kubernetes-terraform')/p.relative_to(examples))
path='docs/quick-reference/kubernetes-terraform-guide.html'
entry={'path':path,'title':'쿠버네티스 · 테라폼 강의 노트 · 기초부터 실습까지','category':'AWS · 클라우드','url':path+'?v='+hashlib.sha256(page.encode()).hexdigest()[:12],'format':'HTML'}
catalog=json.loads((root/'catalog.json').read_text())
catalog=[x for x in catalog if x['path']!=path]
catalog.insert(0,entry)
(root/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
index=(root/'index.html').read_text()
index,n=re.subn(r'const documents = \[.*?\];',lambda _: 'const documents = '+json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+';',index,count=1,flags=re.S)
assert n==1,'catalog integration point not found'
(root/'index.html').write_text(index)
print(f'Built {len(links)} chapters, {len(page):,} HTML characters, downloadable examples, and catalog.')
