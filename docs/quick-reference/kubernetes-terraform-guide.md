# 쿠버네티스 · 테라폼 기초부터 실습까지

처음 배우는 사람을 위한 강의 노트 · 2026-10-16

이 문서는 특정 유료 강의나 영상의 필기본이 아니라 공식 문서를 참고해 새로 구성한 학습 자료입니다. 수강신청 웹 서비스를 예로 들어 **왜 필요한지 → 무엇인지 → 어떻게 연결되는지 → 직접 실행 → 문제 해결** 순서로 설명합니다. 복사 가능한 실습은 로컬 Kubernetes용이며 AWS 유료 자원을 만들지 않습니다.

처음 읽을 때는 모든 용어를 외우지 마세요. “서버를 준비하는 일”과 “그 서버에서 앱을 계속 실행하는 일”을 구분하는 것이 출발점입니다.

## 01. 두 기술의 역할부터 구분하기

학교 수강신청 사이트를 운영한다고 생각해 봅시다. 사용자는 브라우저로 접속하고, 서버는 강의 목록을 읽어 오며, 데이터베이스는 신청 내역을 저장합니다. 이를 운영하려면 두 종류의 일이 필요합니다.

- **실행 기반 준비:** 네트워크, 서버, 저장소, 데이터베이스, 클러스터 등을 준비합니다.
- **애플리케이션 운영:** 어떤 이미지를 실행할지, 몇 개 실행할지, 장애가 나면 어떻게 복구할지 결정합니다.

Terraform은 첫 번째 일을 코드로 관리하는 데 널리 쓰입니다. Kubernetes는 두 번째 일인 컨테이너 워크로드 운영을 담당합니다. Terraform은 Kubernetes provider를 통해 클러스터 내부 객체도 관리할 수 있으므로 두 도구의 경계가 완전히 고정된 것은 아닙니다.

| 질문 | 주로 맡는 도구 | 쉬운 예 |
| --- | --- | --- |
| 네트워크와 실행 환경을 어떻게 만들까? | Terraform | 교실·전기·인터넷을 준비 |
| 앱을 몇 개, 어디에서 실행할까? | Kubernetes | 수업 배정과 운영 |
| 프로그램과 실행에 필요한 파일을 어떻게 포장할까? | 컨테이너 이미지 빌드 도구 | 동일한 실습 교재 묶음 제작 |
| 코드를 변경할 때마다 어떻게 검사하고 배포할까? | CI/CD | 제출→검사→배포 절차 자동화 |

**기억할 문장:** Terraform은 원하는 자원 구성을 계획하고 적용합니다. Kubernetes는 클러스터 안에서 원하는 실행 상태를 지속적으로 맞춥니다. 일반적인 Terraform CLI는 실행하지 않는 동안 계속 감시·복구하는 데몬이 아닙니다. [Terraform 소개](https://developer.hashicorp.com/terraform/intro)

## 02. 서버·가상머신·컨테이너·이미지

**서버**는 요청을 받아 일을 처리하는 컴퓨터 또는 프로그램입니다. **가상머신(VM)**은 가상 하드웨어 위에서 별도의 운영체제를 실행합니다. **컨테이너**는 프로세스를 격리하고 호스트 커널을 공유하는 실행 방식입니다. 컨테이너가 “운영체제 없는 가상머신”이라고만 외우면 실제 구조를 놓치기 쉽습니다.

**이미지**는 실행할 프로그램과 필요한 파일을 담은 읽기 전용 기반입니다. **컨테이너**는 이미지를 바탕으로 실제 실행한 인스턴스입니다. 같은 이미지에서 여러 컨테이너를 만들 수 있습니다.

예를 들어 `campus-api:1.0`이라는 이미지가 있다면, 그 이미지로 API 서버를 세 개 실행할 수 있습니다. 이미지는 설계된 실행 묶음이고 세 컨테이너는 각각 실행 중인 프로그램입니다. 앱 소스를 바꾸었다고 실행 중인 컨테이너가 자동으로 새 코드가 되는 것은 아닙니다. 새 이미지를 만들고 배포해야 합니다.

이미지 이름의 `:1.0`은 태그입니다. 태그는 저장소에서 다른 이미지로 바뀔 수 있으므로 운영에서 정확한 동일 이미지를 재현하려면 digest로 고정하는 방법도 사용합니다. Kubernetes가 컨테이너를 실행하려면 각 노드에 containerd 같은 컨테이너 런타임이 필요합니다. 개발용 Docker Desktop과 Kubernetes 노드의 런타임을 같은 개념으로 보지 마세요.

## 03. Kubernetes가 해결하는 문제

컨테이너 하나를 실행하는 것 자체는 어렵지 않습니다. 그러나 여러 서버에서 수십 개를 실행하면 다음 문제가 생깁니다.

1. 서버 A의 자원이 부족하면 새 앱은 어디에 놓을까요?
2. 앱 프로세스가 종료되면 누가 다시 실행할까요?
3. 앱을 세 개 실행할 때 사용자의 요청은 어디로 보내야 할까요?
4. 새 버전으로 바꾸는 동안 기존 요청은 어떻게 처리할까요?
5. 설정과 저장 데이터를 앱 교체 이후에도 어떻게 유지할까요?

Kubernetes는 이러한 운영 요구를 API 객체로 표현합니다. 다만 소스 코드의 논리 오류, DB 트랜잭션 오류, 느린 쿼리까지 자동으로 고쳐 주지는 않습니다. 수강신청 중복 방지는 DB 제약과 애플리케이션의 동시성 제어로 해결해야 합니다.

쿠버네티스의 약어 **K8s**는 K와 s 사이에 글자가 8개 있다는 뜻입니다. [워크로드 개요](https://kubernetes.io/docs/concepts/workloads/)

## 04. 선언형 설정과 상태를 맞추는 과정

명령형 표현은 “앱을 실행해. 한 개 더 실행해.”입니다. 선언형 표현은 “앱이 항상 세 개 실행되는 상태를 원한다.”입니다.

Kubernetes는 원하는 상태와 관측한 실제 상태를 비교합니다. 세 개가 필요한데 두 개만 있으면, 관련 컨트롤러가 부족한 하나를 만들도록 동작합니다. 이 과정을 **reconciliation**, 즉 상태를 맞추는 과정이라고 부릅니다.

```text
원하는 상태: Pod 3개
       ↓ 비교
현재 상태: Pod 2개
       ↓ 조정
부족한 Pod 생성
       ↓ 반복 관찰
다시 원하는 상태에 가까워짐
```

이 처리는 즉각 완료되는 한 번의 함수 호출이 아닙니다. API에 요청이 접수된 뒤 스케줄링, 이미지 다운로드, 앱 시작 등이 차례로 진행됩니다. `kubectl apply`가 성공했다는 것과 사용자가 앱에 정상 접속한다는 것은 서로 다른 확인 단계입니다.

Pod를 그냥 단독으로 만들면 삭제 후 자동 복제되는 Deployment의 동작을 기대할 수 없습니다. “자동 복구”는 어떤 상위 관리 객체가 존재하는지와 설정에 따라 달라집니다.

## 05. 클러스터 내부 구조

**클러스터**는 Kubernetes가 관리하는 전체 실행 환경입니다. **노드**는 그 환경에 참여하는 머신입니다. 한 머신에 제어 역할과 실행 역할을 함께 둘 수도 있지만, 역할은 구분해서 이해합니다.

| 구성 요소 | 하는 일 | 비유 |
| --- | --- | --- |
| API Server | 설정·조회·변경 요청의 중심 API | 행정 접수 창구 |
| etcd | 클러스터 API 상태를 저장 | 운영 장부 |
| Scheduler | 아직 노드가 정해지지 않은 Pod를 배치 | 자리 배정 담당 |
| Controller Manager | 여러 컨트롤러의 조정 루프 실행 | 상태 확인 담당 |
| kubelet | 노드에서 Pod 실행 상태 관리 | 현장 담당자 |
| 컨테이너 런타임 | 이미지로 컨테이너 실행 | 실제 실행 장치 |
| 네트워크 구현 | Pod 통신과 Service 전달 지원 | 통신망 |

kube-proxy는 Service 네트워크를 구현하는 일반적인 구성 요소지만 다른 네트워크 구현으로 그 기능을 대체할 수 있습니다. etcd는 수강신청 업무 데이터를 저장하는 PostgreSQL의 대체품이 아닙니다. [Kubernetes 구성 요소](https://kubernetes.io/docs/concepts/overview/components/)

## 06. Pod는 컨테이너를 감싸는 실행 단위

Kubernetes가 배치하는 기본 단위는 **Pod**입니다. Pod에는 하나 이상의 컨테이너가 들어갑니다. 같은 Pod 안의 컨테이너는 네트워크 공간을 공유하고, 정의한 볼륨을 함께 사용할 수 있습니다.

입문에서는 “Pod 하나에 주 애플리케이션 컨테이너 하나”로 시작하면 이해하기 쉽습니다. 보조 컨테이너가 필요한 경우에 여러 컨테이너를 묶습니다. 서로 독립적으로 늘리고 줄여야 하는 웹 서버와 DB를 단지 편하다는 이유로 같은 Pod에 넣지는 않습니다.

Pod가 교체되면 이름이나 IP가 달라질 수 있습니다. 따라서 앱이 특정 Pod IP를 영구 주소로 기억하도록 만들면 취약합니다. 안정적인 접근에는 Service를 사용합니다.

**자주 하는 오해:** “Pod를 세 개 만들면 각각 다른 서버에 자동 분산된다.” 반드시 그렇지는 않습니다. 노드 자원과 스케줄링 규칙에 따라 같은 노드에 배치될 수 있습니다. 노드 또는 가용 영역 분산이 중요하면 topology spread constraints 같은 정책을 별도로 설계해야 합니다. [Pod 개념](https://kubernetes.io/docs/concepts/workloads/pods/)

## 07. Deployment·ReplicaSet의 관계

Deployment는 주로 교체 가능한 애플리케이션 복제본과 버전 업데이트를 관리합니다. Deployment가 ReplicaSet을 관리하고 ReplicaSet이 지정된 수의 Pod를 유지합니다.

```text
Deployment: 어떤 버전·어떤 배포 전략인가?
  └─ ReplicaSet: 이 템플릿의 Pod가 몇 개 필요한가?
       ├─ Pod A
       ├─ Pod B
       └─ Pod C
```

`replicas: 3`은 Pod의 목표 개수입니다. `template`은 새 Pod를 만들 때 사용할 설계입니다. 이미지를 변경하면 Pod 템플릿이 달라지므로 새 ReplicaSet을 이용한 롤아웃이 진행됩니다. 단순히 replicas만 바꾸는 것은 이미지 버전 업데이트와 다릅니다.

Pod 하나가 사라져도 ReplicaSet이 부족한 수를 채울 수 있습니다. 다만 노드 자원이 부족하거나 이미지를 받을 수 없으면 새 Pod는 정상 실행되지 못합니다. 자동 생성이 곧 자동 성공을 뜻하지는 않습니다. [Deployment 공식 문서](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

## 08. YAML 파일 읽는 순서

Kubernetes 설정 파일을 보통 manifest라고 부릅니다. 다음 네 부분부터 봅니다.

| 키 | 의미 | 확인할 질문 |
| --- | --- | --- |
| `apiVersion` | 해당 객체 API의 버전 | 어떤 API를 사용하는가? |
| `kind` | 객체 종류 | Deployment인가 Service인가? |
| `metadata` | 이름·namespace·labels 등 | 누구이며 어디에 속하는가? |
| `spec` | 원하는 동작 | 어떤 상태를 원하는가? |

YAML에서 들여쓰기는 구조입니다. 탭 대신 공백을 사용합니다. `-`는 목록 항목이고 `키: 값`은 속성입니다. `---`는 한 파일 안의 문서 구분입니다. `#` 뒤는 주석입니다.

`metadata.name`은 객체의 이름이고, `labels`는 검색·선택용 표식입니다. 이름이 같아도 namespace가 다르면 별개의 namespaced 객체일 수 있습니다. 반대로 Node 같은 객체는 특정 namespace에 속하지 않습니다.

## 09. Label·Selector·Namespace

강의실에 “백엔드반”이라는 표식을 붙이는 것이 label입니다. “백엔드반 표식이 있는 강의실을 선택한다”가 selector입니다.

```yaml
metadata:
  labels:
    app: lecture-web
```

Service의 `selector: { app: lecture-web }`는 그 label이 있는 Pod를 대상으로 삼습니다. `Deployment.metadata.labels`에만 표식을 붙이고 `Deployment.spec.template.metadata.labels`에 붙이지 않으면 Pod의 label은 원하는 값이 되지 않습니다.

Namespace는 한 클러스터 안의 논리적인 구획입니다. 실습에서는 `lecture-demo`, Terraform 연동에서는 `lecture-tf`를 사용합니다. 이렇게 나누면 어느 도구가 무엇을 관리하는지 분명해집니다. Namespace만 나눈다고 네트워크나 권한이 자동으로 완전히 격리되는 것은 아닙니다. 실제 격리에는 RBAC, NetworkPolicy, 자원 제한 등을 함께 검토합니다.

## 10. Service와 세 종류의 포트

Service는 교체되는 Pod 집합에 접근할 수 있는 안정적인 주소와 포트를 제공합니다. 일반적인 label selector 방식에서는 선택된 Pod들의 엔드포인트를 바탕으로 트래픽 전달이 이뤄집니다.

| 종류 | 주요 목적 | 입문에서 주의할 점 |
| --- | --- | --- |
| ClusterIP | 클러스터 내부 접근 | 기본 타입, 외부 공개 아님 |
| NodePort | 노드의 특정 포트로 접근 | 방화벽·네트워크 경로도 필요 |
| LoadBalancer | 외부 로드밸런서 연계 | 지원 구현 필요, 환경에 따라 비용 발생 |
| ExternalName | 외부 DNS 이름에 대한 별칭 | 일반적인 Pod 선택 방식과 다름 |

`port`는 Service가 받는 포트, `targetPort`는 Pod의 앱이 받는 포트입니다. `containerPort`는 컨테이너 포트의 선언이며 그 자체가 앱을 실행하거나 방화벽을 여는 명령은 아닙니다.

예를 들어 Service의 `port: 80`, `targetPort: 8080`이면 “서비스의 80으로 온 요청을 앱의 8080으로 보낸다”입니다. 같은 namespace의 Pod는 일반적으로 Service 이름으로 접근할 수 있습니다. [Service 공식 문서](https://kubernetes.io/docs/concepts/services-networking/service/)

## 11. Ingress·Gateway·DNS·HTTPS

Service는 앱 집합으로 접근하는 기본 통로입니다. 여러 웹 앱을 도메인과 URL 경로에 따라 나누려면 별도의 HTTP 라우팅 계층이 유용합니다.

```text
사용자 → DNS로 주소 조회 → 외부 진입점
                         ↓ 호스트·경로 규칙
                      Service → Pod
```

Ingress 객체는 `school.example/api` 같은 규칙을 표현합니다. 그 규칙을 실제로 처리할 Ingress Controller가 설치되어 있어야 합니다. Ingress YAML만 제출해도 인터넷 공개, DNS 등록, 인증서 발급까지 모두 자동으로 완료되는 것은 아닙니다.

Ingress API는 기능이 동결된 상태이며 Kubernetes 공식 문서는 새 기능을 위한 Gateway API를 안내합니다. Gateway API도 해당 리소스와 호환 컨트롤러가 필요합니다. 어떤 구현을 사용하는지에 따라 설정 방법이 다릅니다. HTTPS는 인증서와 TLS 종료 위치, 앱까지의 통신 경로를 함께 설계합니다. [Ingress와 Gateway 안내](https://kubernetes.io/docs/concepts/services-networking/ingress/)

## 12. ConfigMap과 Secret

앱의 실행 이미지와 환경별 설정은 분리하는 편이 좋습니다. 개발 환경과 운영 환경의 DB 주소가 다르다고 매번 소스를 수정하는 방식은 관리하기 어렵습니다.

| 객체 | 넣는 값의 예 | 사용 방식 |
| --- | --- | --- |
| ConfigMap | 로그 수준, 일반 설정, 화면 문구 | 환경변수 또는 파일 마운트 |
| Secret | 비밀번호, 토큰, 인증서 등 | 권한을 제한하여 주입 |

**Secret의 base64는 암호화가 아닙니다.** API 접근 권한, 저장 시 암호화 설정, 외부 비밀 관리 연동 등을 별도로 고려해야 합니다. 예제라고 실제 비밀번호를 Git에 넣지 않습니다. [Secret 공식 문서](https://kubernetes.io/docs/concepts/configuration/secret/)

환경변수로 주입한 설정은 이미 실행 중인 프로세스에서 자동으로 바뀌지 않습니다. 파일로 마운트한 설정도 앱이 파일 변경을 다시 읽는지 확인해야 합니다. 특히 `subPath` 마운트는 일반적인 ConfigMap 볼륨 업데이트와 동작이 다릅니다. 이 실습은 확실한 확인을 위해 설정 변경 후 Deployment를 재시작합니다.

## 13. 데이터 저장: Volume·PV·PVC

Pod가 사라질 수 있으므로 컨테이너 내부의 쓰기 영역을 영구 저장소처럼 사용하면 안 됩니다. 업로드 파일이나 DB 데이터를 어디에 저장할지 별도로 정해야 합니다.

- **Volume:** 컨테이너에 연결할 저장 공간의 표현입니다.
- **PV:** 클러스터가 사용하는 영구 저장 자원의 표현입니다.
- **PVC:** 애플리케이션이 요구하는 저장 공간의 요청입니다.
- **StorageClass:** 어떤 방식으로 볼륨을 준비할지 나타내는 정책입니다.

식당에 비유하면 PVC는 “10인용 자리 주세요”, PV는 실제 배정되는 자리, StorageClass는 자리 배정 방식입니다. PVC를 만들었다고 항상 즉시 연결되는 것은 아닙니다. 적절한 스토리지 구현, 용량, 접근 모드, 배치 조건이 맞아야 합니다.

`emptyDir`는 같은 Pod 안에서 컨테이너가 재시작되어도 유지될 수 있지만 Pod가 제거되면 사라집니다. PVC를 쓴다고 백업이 자동으로 생기지는 않습니다. 삭제 시 보존 여부는 reclaim policy 등 설정에 따라 달라집니다. [Persistent Volume](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

## 14. requests·limits와 상태 검사

`requests`는 스케줄러가 배치할 때 기준으로 삼는 자원 요청량입니다. `limits`는 컨테이너가 사용할 수 있는 상한을 정합니다. CPU `100m`은 0.1 CPU, `500m`은 0.5 CPU입니다. 메모리 `128Mi`는 이진 단위의 128 mebibytes입니다.

CPU 제한에 도달하면 보통 실행이 제한되는 throttling이 생깁니다. 메모리 제한을 넘으면 OOM 종료가 발생할 수 있습니다. 요청량이 너무 크면 배치할 노드가 없어 Pending이 될 수 있고, 너무 작으면 실제 부하를 충분히 반영하지 못할 수 있습니다. [컨테이너 자원 관리](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

| 검사 | 질문 | 실패 시 주요 효과 |
| --- | --- | --- |
| startupProbe | 처음 실행 준비가 끝났나? | 임계값 초과 시 해당 컨테이너 재시작 |
| readinessProbe | 지금 새 요청을 받아도 되나? | 일반적인 Service 트래픽 대상에서 제외 |
| livenessProbe | 프로세스가 복구 불가능하게 멈췄나? | 임계값 초과 시 해당 컨테이너 재시작 |

startupProbe가 설정되면 성공하기 전에는 readiness/liveness 검사가 시작되지 않습니다. Readiness 실패 자체가 컨테이너를 재시작시키는 것은 아닙니다. 외부 DB 일시 장애를 liveness 실패로 연결하면 모든 앱을 불필요하게 재시작할 수도 있으므로 검사 의미를 구분하세요. [Probe 공식 설명](https://kubernetes.io/docs/concepts/workloads/pods/probes/)

## 15. 배포·롤백·자동 확장

RollingUpdate는 새 Pod를 조금씩 만들고 기존 Pod를 줄이는 배포 방식입니다. `maxSurge`는 목표 개수보다 추가로 허용할 Pod 수, `maxUnavailable`은 업데이트 중 허용할 가용 복제본 부족 수를 나타냅니다.

`maxUnavailable: 0`이라고 완전한 무중단이 보장되는 것은 아닙니다. Readiness, 충분한 추가 용량, 종료 시 연결 정리, 세션 공유, 이전·새 버전의 DB 호환성이 함께 필요합니다. Deployment가 실패했다고 항상 자동으로 이전 버전으로 돌아가는 것도 아닙니다. 롤아웃 상태를 확인하고 필요하면 명시적으로 롤백합니다.

**HPA**는 지표를 보고 Pod 수를 조절합니다. CPU 사용률 기반 방식은 해당 컨테이너의 CPU requests와 metrics API 준비가 중요합니다. HPA가 Pod를 늘려도 노드 용량이 부족하면 Pending이 됩니다. 노드 자체를 늘리는 기능은 별도의 노드 자동 확장 계층입니다. [HPA 공식 문서](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/)

Deployment 외에도 StatefulSet은 안정적인 식별자와 저장소가 필요한 앱, DaemonSet은 해당 노드마다 필요한 에이전트, Job은 완료되는 작업, CronJob은 주기적인 작업에 사용합니다. StatefulSet을 사용한다고 DB 복제·백업이 자동 구성되지는 않습니다.

## 16. 실습 준비: 기존 환경과 분리하기

실습에는 컨테이너 실행 환경, `kind`, `kubectl`이 필요합니다. kind는 로컬 컨테이너를 Kubernetes 노드로 사용하는 학습·테스트 도구입니다. 운영 클러스터 구축 도구로 생각하지 마세요. 아래 명령은 macOS/Linux의 bash 또는 zsh 기준입니다. Windows에서는 WSL2 등 적절한 셸 환경에 맞춰 경로를 조정합니다.

먼저 [kind 설치 안내](https://kind.sigs.k8s.io/docs/user/quick-start/)와 [kubectl 설치 안내](https://kubernetes.io/docs/tasks/tools/)에 따라 도구를 준비합니다. Docker Desktop 등을 실행한 뒤 아래를 확인합니다.

```sh
docker info
kind version
kubectl version --client
```

다운로드한 예제 폴더 `kubernetes-terraform`에서 시작합니다. 클러스터 이름과 kubeconfig 파일이 이미 있다면 기존 실습인지 확인한 뒤 이름을 바꾸거나 재사용하세요. 아래는 이 이름을 처음 사용하는 경우입니다.

```sh
mkdir -p "$HOME/.kube"
kind create cluster --name lecture-local --kubeconfig "$HOME/.kube/lecture-kind.yaml"
export KUBECONFIG="$HOME/.kube/lecture-kind.yaml"
kubectl config current-context
kubectl get nodes
```

예상 context는 `kind-lecture-local`입니다. 노드가 `Ready`인지 확인합니다. 새 터미널을 열면 `export KUBECONFIG=...`를 다시 실행해야 합니다. 전용 kubeconfig 파일을 사용하므로 기본 파일을 실습용으로 덮어쓸 필요가 없습니다.

## 17. Kubernetes 실습: 전체 YAML과 해설

실행 파일: [kubernetes/demo.yaml](sample-files/kubernetes-terraform/kubernetes/demo.yaml). 이 예제의 이미지 태그는 학습 재현을 위한 예시이며 최신 버전 또는 운영 보안 기준을 뜻하지 않습니다. 실제 운영에는 검증한 이미지 digest와 보안 정책을 적용합니다.


```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: lecture-demo
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: lecture-page
  namespace: lecture-demo
data:
  index.html: |
    <!doctype html>
    <html lang="ko">
    <head><meta charset="utf-8"><title>Kubernetes 실습</title></head>
    <body><h1>쿠버네티스 첫 배포 성공</h1><p>ConfigMap으로 제공하는 페이지입니다.</p></body>
    </html>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lecture-web
  namespace: lecture-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lecture-web
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: lecture-web
    spec:
      containers:
        - name: nginx
          image: nginx:1.28.0-alpine
          ports:
            - name: http
              containerPort: 80
          resources:
            requests:
              cpu: 100m
              memory: 32Mi
            limits:
              cpu: 500m
              memory: 128Mi
          startupProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 2
            failureThreshold: 30
          readinessProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 10
          volumeMounts:
            - name: page
              mountPath: /usr/share/nginx/html
              readOnly: true
      volumes:
        - name: page
          configMap:
            name: lecture-page
---
apiVersion: v1
kind: Service
metadata:
  name: lecture-web
  namespace: lecture-demo
spec:
  type: ClusterIP
  selector:
    app: lecture-web
  ports:
    - name: http
      port: 80
      targetPort: http
```


코드를 위에서부터 읽어 봅시다.

1. Namespace는 `lecture-demo`라는 구획을 만듭니다.
2. ConfigMap의 `index.html`은 웹에서 보여 줄 문서입니다. YAML의 `|`는 여러 줄 문자열을 뜻합니다.
3. Deployment는 `replicas: 2`로 같은 앱을 두 개 실행합니다.
4. `selector.matchLabels`와 Pod 템플릿의 labels가 일치해야 합니다.
5. 컨테이너는 Nginx 이미지를 실행하고 이름이 `http`인 80번 포트를 선언합니다.
6. 자원 요청과 제한으로 배치 기준 및 사용 상한을 지정합니다.
7. HTTP `/`에 대한 세 가지 검사로 시작·트래픽 수신·생존 상태를 구분합니다.
8. ConfigMap을 `/usr/share/nginx/html`에 연결해 기본 페이지를 바꿉니다.
9. Service는 `app: lecture-web`인 Pod를 선택하고 이름이 `http`인 포트로 전달합니다.

전용 실습 클러스터에서 다음을 실행합니다.

```sh
kubectl apply -f kubernetes/demo.yaml
kubectl -n lecture-demo rollout status deployment/lecture-web --timeout=120s
kubectl -n lecture-demo get deployments,replicasets,pods,services
kubectl -n lecture-demo port-forward service/lecture-web 8080:80
```

마지막 명령을 실행한 터미널은 그대로 두고 브라우저에서 `http://localhost:8080`을 엽니다. “쿠버네티스 첫 배포 성공”이 보이면 됩니다. `8080:80`은 내 컴퓨터 8080을 Service의 80으로 연결한다는 뜻입니다. 8080을 다른 앱이 사용하면 `8081:80`으로 바꾸고 8081로 접속합니다.

**port-forward는 학습용 접근 통로입니다.** 이 실습으로 외부 로드밸런서의 분산 동작까지 검증했다고 해석하지 마세요. 특히 Service를 대상으로 한 port-forward도 실제로 선택된 한 Pod에 연결됩니다. 중단은 해당 터미널에서 Ctrl+C입니다.

## 18. 실습 확장: 복구·설정 변경·배포 확인

다른 터미널에서 먼저 전용 kubeconfig를 지정합니다.

```sh
export KUBECONFIG="$HOME/.kube/lecture-kind.yaml"
kubectl -n lecture-demo get pods -l app=lecture-web
```

화면에 나온 Pod 이름 하나를 복사하여 다음 명령의 `POD_NAME`을 바꿉니다. 이 이름은 예시 자리표시자이므로 그대로 실행하지 않습니다.

```sh
kubectl -n lecture-demo delete pod POD_NAME
kubectl -n lecture-demo get pods -w
```

새 이름의 Pod가 생기는 것을 관찰한 뒤 Ctrl+C로 조회를 끝냅니다. 기존 port-forward가 그 Pod에 붙어 있었다면 끊어질 수 있으므로 다시 실행합니다. 이 실험의 핵심은 “같은 Pod가 부활”하는 것이 아니라 “관리자가 새 Pod로 목표 개수를 채움”입니다.

복제본 수를 바꾸려면 `demo.yaml`의 `replicas: 2`를 `3`으로 수정하고 다시 apply합니다. 화면 문구는 같은 파일의 ConfigMap에서 수정합니다.

```sh
kubectl apply -f kubernetes/demo.yaml
kubectl -n lecture-demo rollout restart deployment/lecture-web
kubectl -n lecture-demo rollout status deployment/lecture-web --timeout=120s
```

ConfigMap 변경 자체는 Deployment의 Pod 템플릿 변경이 아니므로 새 롤아웃을 자동으로 만들지 않습니다. 이 절에서는 restart를 명시해 새 설정을 읽는 과정을 확인합니다.

이미지를 검증한 다른 태그로 바꾸면 롤아웃이 일어납니다. 다음 명령은 이력을 확인하거나 이전 Pod 템플릿으로 돌아갈 때 사용합니다.

```sh
kubectl -n lecture-demo rollout history deployment/lecture-web
# 이전 revision이 존재하고 실제로 되돌릴 필요가 있을 때만 실행
kubectl -n lecture-demo rollout undo deployment/lecture-web
```

롤백은 ConfigMap 내용이나 DB 데이터까지 되돌리는 기능이 아닙니다. 또한 파일의 이미지 값도 원래 원하는 버전으로 맞춰야 다음 apply에서 다시 바뀌지 않습니다.

## 19. Kubernetes 오류를 읽는 순서

오류가 생겼을 때 YAML을 무작정 고치기보다 **현재 상태 → 이벤트 → 앱 로그 → 연결 경로**를 확인합니다.

```sh
kubectl -n lecture-demo get pods -o wide
kubectl -n lecture-demo describe pod POD_NAME
kubectl -n lecture-demo logs POD_NAME
kubectl -n lecture-demo logs POD_NAME --previous
kubectl -n lecture-demo get events --sort-by=.metadata.creationTimestamp
kubectl -n lecture-demo get endpointslices -l kubernetes.io/service-name=lecture-web
```

`--previous`는 이전에 종료된 컨테이너 인스턴스 로그가 남아 있을 때 유용합니다. 실행 이력이 없으면 조회할 로그도 없습니다.

| 증상 | 의미·가능한 원인 | 먼저 볼 것 |
| --- | --- | --- |
| Pending | 아직 실행 준비가 안 됨 | 배치 자원 부족, PVC, 노드 조건, 이벤트 |
| ImagePullBackOff | 이미지 다운로드 재시도 대기 | 저장소·태그·인증·네트워크 |
| CrashLoopBackOff | 반복 종료 후 재시작 대기 | 이전 로그, 종료 코드, 설정 |
| OOMKilled | 메모리 부족으로 종료 | limits, 실제 메모리, 누수 |
| Running인데 Ready가 아님 | 프로세스는 있지만 수신 준비 안 됨 | readiness 경로·포트·응답 |
| Service로 접속 불가 | 대상 또는 전달 경로 문제 | selector, EndpointSlice, targetPort |
| localhost 접속 불가 | 포워딩이 없거나 종료됨 | port-forward 터미널과 포트 충돌 |
| Forbidden | API 권한 부족 | 현재 context와 RBAC 권한 |
| PVC Pending | 적절한 저장소 연결 대기 | StorageClass, provisioner, 배치 조건 |

`kubectl get all`은 이름과 달리 모든 종류의 객체를 보여 주지 않습니다. ConfigMap, Secret, PVC 등은 필요에 따라 별도로 조회합니다.

## 20. Terraform의 핵심: 코드를 자원 변경으로 바꾸기

인프라를 웹 콘솔에서 수동으로 만들면 지금 어떤 설정인지, 누가 무엇을 바꾸었는지 재현하기 어려울 수 있습니다. Terraform은 원하는 자원을 텍스트로 선언하고 그 차이를 계획합니다. 이 접근을 **Infrastructure as Code, IaC**라고 부릅니다.

흐름은 `작성 → 초기화 → 형식·구조 검사 → 변경 계획 확인 → 적용 → 실제 동작 확인`입니다. 코드를 Git으로 관리하면 변경 이유와 검토 기록을 남길 수 있습니다. 다만 Git에 코드가 있다고 이미 배포되었다는 뜻은 아닙니다. [Terraform 작업 흐름](https://developer.hashicorp.com/terraform/intro/core-workflow)

Kubernetes YAML과 Terraform HCL은 모두 원하는 구성을 표현할 수 있지만, 문법과 관리 주체가 다릅니다. Terraform의 `.tf`는 HCL 기반이며 보통 Kubernetes manifest는 YAML로 작성합니다.

## 21. HCL 블록을 읽는 법

```hcl
resource "terraform_data" "lesson" {
  input = {
    name     = "lecture-dev"
    replicas = 2
  }
}
```

이 코드의 `resource`는 관리할 자원을 선언한다는 뜻입니다. 첫 문자열 `terraform_data`는 타입, 두 번째 문자열 `lesson`은 코드 안에서 쓰는 이름입니다. 전체 주소는 `terraform_data.lesson`입니다. 이 이름이 반드시 외부 서비스에 표시되는 이름과 같지는 않습니다.

중괄호 안에는 해당 타입의 설정을 씁니다. `=`는 속성에 값을 지정하고, 문자열은 따옴표, 숫자는 따옴표 없이 표현합니다. 위의 `replicas = 2`는 학습 데이터일 뿐 실제 Pod 두 개를 만드는 코드가 아닙니다. 어떤 자원을 만드는지는 resource 타입과 provider가 결정합니다.

| 표현 | 의미 | 예 |
| --- | --- | --- |
| string | 문자열 | `"dev"` |
| number | 숫자 | `2` |
| bool | 참·거짓 | `true` |
| list | 순서 있는 목록 | `["web", "api"]` |
| map/object | 키로 구분한 값 묶음 | `{ name = "web", port = 80 }` |
| 참조 | 다른 값 사용 | `var.replicas` |
| 문자열 보간 | 문자열 안에 값 삽입 | `"lecture-${var.environment}"` |

Terraform은 `.tf` 파일을 파일명 순서대로 실행하는 스크립트가 아닙니다. 같은 디렉터리의 설정을 하나의 모듈로 읽고 참조 관계를 바탕으로 의존성을 계산합니다. `main.tf`, `variables.tf`, `outputs.tf`는 사람이 읽기 좋게 나눈 관례입니다.

## 22. Provider·Resource·Data Source·Variable·Output

| 요소 | 쉬운 뜻 | 사용하는 이유 |
| --- | --- | --- |
| provider | 외부 API와 대화하는 연결 도구 | AWS·Kubernetes 등과 통신 |
| resource | Terraform이 관리할 객체 | 생성·변경·삭제 계획 |
| data source | 기존 정보를 조회 | 이미 있는 값 또는 외부 정보를 참조 |
| variable | 모듈이 받는 입력 | 환경마다 다른 값 전달 |
| locals | 내부 계산값에 붙인 이름 | 중복 계산 줄이기 |
| output | 모듈이 내보내는 결과 | 주소·식별자 등 전달 |
| module | 관련 설정의 재사용 단위 | 표준 구성 묶기 |

Provider의 종류는 `required_providers`, 연결 설정은 `provider` 블록에 둡니다. provider 버전과 Terraform CLI 버전은 별개입니다. `required_version`은 Terraform 자체 버전 조건입니다.

Data source로 자원을 조회했다고 Terraform이 그 자원의 삭제까지 소유하게 되는 것은 아닙니다. 또한 data source가 항상 모든 실행보다 먼저 조회되는 것도 아닙니다. 입력값이 적용 후 결정되는 경우 읽기가 뒤로 미뤄질 수 있습니다.

Variable에는 type, default, description, validation을 지정할 수 있습니다. 값은 `.tfvars`, 환경변수 `TF_VAR_변수명`, CLI 옵션 등으로 전달합니다. 이 문서의 실습에서는 흐름을 쉽게 확인하도록 `-var`를 사용합니다. [입력 변수](https://developer.hashicorp.com/terraform/language/values/variables)

## 23. init·fmt·validate·plan·apply

| 명령 | 하는 일 | 하지 않는 일 |
| --- | --- | --- |
| `terraform init` | backend·provider·module 준비 | 원하는 서버를 바로 생성하지 않음 |
| `terraform fmt` | 코드 형식을 정리 | 인프라의 올바름을 보증하지 않음 |
| `terraform validate` | 설정 구조와 타입 등 검사 | 실제 계정 권한·가용 용량을 보증하지 않음 |
| `terraform plan` | 관측한 상태와 구성을 비교해 계획 | 계획한 변경을 적용하지 않음 |
| `terraform apply` | 계획한 변경 실행 | 앱의 모든 기능이 정상임을 보증하지 않음 |
| `terraform output` | 저장된 출력값 표시 | 외부 서비스 상태 실시간 감시 아님 |
| `terraform destroy` | 관리 대상 삭제 계획·실행 | 현재 계정의 모든 자원을 무조건 삭제하는 명령 아님 |

`plan`은 일반적으로 provider를 통해 실제 상태도 조회합니다. 그래서 plan만 해도 네트워크와 읽기 권한이 필요할 수 있습니다. 저장된 plan을 적용하려면 다음처럼 실행합니다.

```sh
terraform plan -out=lesson.tfplan
terraform show lesson.tfplan
terraform apply lesson.tfplan
```

**저장된 plan을 지정한 apply는 별도의 yes 확인을 다시 요구하지 않습니다.** 따라서 적용 전에 내용을 검토해야 합니다. 파일 없이 `terraform apply`를 하면 새 계획을 만들고 일반적으로 확인을 받습니다. 오래된 plan은 상태 변화로 적용이 거부될 수 있으므로 최신 상황에서 다시 계획하세요. [CLI 작업 흐름](https://developer.hashicorp.com/terraform/cli/run)

## 24. State: 구성과 실제 객체를 연결하는 기록

설정 코드는 “내가 원하는 것”, 실제 환경은 “지금 존재하는 것”, state는 “이 코드의 자원이 어떤 실제 객체와 연결되는지 기록한 것”입니다.

예를 들어 `kubernetes_deployment_v1.web`이라는 코드 주소가 특정 namespace의 Deployment에 연결되었다는 정보를 state가 기억합니다. state를 잃으면 기존 객체가 자동 삭제되는 것은 아니지만 Terraform이 연결 관계를 잃을 수 있습니다. 그대로 새로 apply하면 중복 생성 시도나 충돌이 발생할 수 있습니다.

State는 단순 로그나 불필요한 캐시가 아닙니다. 임의로 지워 오류를 해결하려 하지 마세요. 팀에서는 원격 backend, 접근 제어, 버전 보관, 해당 backend가 지원하는 잠금을 검토합니다. 잠금은 여러 작업이 동시에 state를 갱신하는 충돌을 줄입니다. [State 공식 문서](https://developer.hashicorp.com/terraform/language/state)

**두 종류의 lock은 다릅니다.** `.terraform.lock.hcl`은 provider 선택 버전과 체크섬을 기록하는 의존성 잠금 파일이며 보통 Git에 넣습니다. state lock은 동시에 state를 바꾸지 못하도록 하는 실행 중 조정 장치입니다. module 버전까지 `.terraform.lock.hcl`이 모두 고정해 주는 것은 아닙니다. [의존성 잠금 파일](https://developer.hashicorp.com/terraform/language/files/dependency-lock)

State와 저장된 plan에는 민감한 값이 들어갈 수 있으므로 공개 저장소에 올리지 않습니다. `sensitive = true`는 일반 출력의 노출을 줄이는 표시이며, 그것만으로 state의 값이 암호화되거나 저장되지 않는 것은 아닙니다. [민감한 값 관리](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)

## 25. Terraform 첫 실습: 클라우드 계정 없이 상태 배우기

먼저 실제 서버를 만들지 않는 `terraform_data`로 변수, 계획, 적용, state를 익힙니다. 이 자원은 Terraform 내장 provider가 제공하며 별도의 클라우드 계정이나 외부 provider 다운로드가 필요하지 않습니다. Terraform 1.4 이상이 필요합니다. [terraform_data 설명](https://developer.hashicorp.com/terraform/language/resources/terraform-data)

실행 파일: [terraform-basics/main.tf](sample-files/kubernetes-terraform/terraform-basics/main.tf)


```hcl
terraform {
  required_version = ">= 1.4, < 2.0"
}

variable "environment" {
  description = "학습 환경 이름"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment는 dev, stage, prod 중 하나여야 합니다."
  }
}

variable "replicas" {
  description = "앱 복제본 목표를 표현하는 학습용 숫자"
  type        = number
  default     = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 5 && floor(var.replicas) == var.replicas
    error_message = "replicas는 1부터 5 사이의 정수여야 합니다."
  }
}

locals {
  app_name = "lecture-${var.environment}"
}

resource "terraform_data" "lesson" {
  input = {
    name     = local.app_name
    replicas = var.replicas
  }
}

output "lesson" {
  description = "state에 기록된 학습용 결과. 실제 서버나 Pod는 만들지 않습니다."
  value       = terraform_data.lesson.output
}
```


`environment`는 입력값, `local.app_name`은 계산값, `terraform_data.lesson`은 관리 객체, `output.lesson`은 보여 줄 결과입니다. `validation`은 허용한 범위를 벗어나는 입력을 거절합니다. `floor(...) == ...` 조건은 소수점 복제본을 막습니다.

예제 루트에서 다음을 실행합니다.

```sh
cd terraform-basics
terraform init
terraform fmt -check
terraform validate
terraform plan -out=lesson.tfplan
terraform show lesson.tfplan
terraform apply lesson.tfplan
terraform output
terraform state list
terraform plan
```

첫 계획에서는 자원 하나를 추가한다는 결과가 예상됩니다. 적용 후에는 `lecture-dev`와 `replicas = 2`를 확인할 수 있습니다. 마지막 plan은 같은 설정에서 일반적으로 `No changes`를 보여 줍니다. 이때 실제 웹 서버나 Pod는 생기지 않았습니다.

값을 변경하면 무엇이 달라지는지 확인합니다.

```sh
terraform plan -var='replicas=3' -out=lesson.tfplan
terraform show lesson.tfplan
terraform apply lesson.tfplan
terraform output
```

이제 state의 학습 데이터가 3으로 바뀝니다. 단, CLI의 `-var`는 다음 실행까지 자동 저장되는 설정이 아닙니다. 이후 `terraform plan`만 실행하면 기본값 2로 되돌리는 변경이 나타날 수 있습니다. 계속 3을 사용하려면 코드의 default 또는 별도 변수 파일로 의도를 명시하세요.

잘못된 값을 넣는 연습도 해봅니다.

```sh
terraform plan -var='replicas=0'
```

예상 결과는 validation 오류입니다. 유효한 자원을 생성한 뒤 실패한 것이 아니라, 잘못된 입력을 계획 과정에서 발견한 것입니다. 실습이 끝나면 `terraform destroy`를 실행하고 표시된 삭제 대상이 이 학습 자원 하나인지 확인한 뒤 승인합니다. 이 예제에서는 state의 학습 객체만 제거됩니다.

## 26. 변경 계획에서 반드시 읽을 표시

| 표시 | 의미 | 생각할 점 |
| --- | --- | --- |
| `+` | 생성 | 새로 필요한 자원인가? |
| `~` | 제자리 변경 | 중단·재시작 영향이 있는가? |
| `-` | 삭제 | 데이터나 연결을 잃지 않는가? |
| `-/+` | 삭제 후 새로 생성 | 잠깐 비는 구간이 생길 수 있는가? |
| `+/-` | 새로 생성 후 기존 삭제 | 중복 용량·이름 충돌이 가능한가? |
| `(known after apply)` | 적용 후 결정되는 값 | 오류가 아니라 아직 미확정인 값인가? |

같은 파일에서 한 줄을 수정해도 해당 provider 속성이 제자리 변경을 지원하지 않으면 교체가 계획될 수 있습니다. 그러므로 “파일 한 줄만 바꿨으니 안전하다”보다 **실제 plan에 어떤 자원 변경이 나오는지**가 중요합니다.

Terraform apply는 전체 작업을 DB 트랜잭션처럼 원자적으로 되돌려 주지 않습니다. 여러 자원 중 일부가 생성된 다음 다른 자원에서 실패할 수 있습니다. 원인을 해결하고 다시 plan하여 이미 완료된 상태를 반영해야 합니다. 무조건 state를 지우거나 destroy부터 실행하지 마세요.

## 27. 의존성·반복·함수·모듈

다음 참조는 “Namespace가 있어야 Deployment를 그 안에 만들 수 있다”는 관계를 표현합니다.

```hcl
namespace = kubernetes_namespace_v1.lecture.metadata[0].name
```

Terraform은 이런 참조에서 의존성을 추론합니다. 파일 이름을 `01-namespace.tf`, `02-app.tf`로 만들었다고 실행 순서가 강제되는 것은 아닙니다. 값 참조만으로 드러나지 않는 의존성에는 `depends_on`을 고려하지만 모든 자원에 붙일 필요는 없습니다.

여러 개를 만들 때 `count`는 숫자 인덱스, `for_each`는 키로 구분하는 방식을 사용합니다. 다음은 개념 설명용이며 첫 실습 파일에 자동 포함되는 코드는 아닙니다.

```hcl
resource "terraform_data" "classroom" {
  for_each = {
    frontend = 2
    backend  = 3
  }
  input = {
    name     = each.key
    students = each.value
  }
}
```

주소는 `terraform_data.classroom["frontend"]`처럼 됩니다. `count`에서 목록 중간을 지우면 뒤 인덱스와 대상의 대응이 바뀔 수 있으므로 안정적인 이름이 있는 자원은 `for_each`가 유리할 수 있습니다. `for_each`의 키는 계획할 때 알아야 하며 민감한 값을 키로 쓰지 않습니다. [for_each](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

자주 보는 함수는 `length`(길이), `merge`(맵 병합), `toset`(집합 변환), `jsonencode`(JSON 생성), `templatefile`(템플릿 렌더링)입니다. 함수는 주로 값을 계산하는 도구입니다. 이름이 함수처럼 생겼다고 외부 서버를 생성하는 것은 아닙니다.

Module은 관련 `.tf` 설정 묶음입니다. 입력 variable과 결과 output을 통해 재사용합니다. 로컬 디렉터리의 `.tf` 파일도 root module을 구성합니다. 네트워크 module, 앱 module처럼 책임을 구분하되 처음부터 모든 자원을 한 줄짜리 module로 나누면 읽기가 오히려 어려워질 수 있습니다. [Module 공식 문서](https://developer.hashicorp.com/terraform/language/modules)

## 28. Drift·Import·리팩터링

**Drift**는 코드가 기대하는 상태와 외부에서 바뀐 실제 상태 사이의 차이입니다. 예를 들어 콘솔에서 복제본 수를 바꾸면 다음 plan에서 Terraform이 이를 관찰하고 구성값으로 되돌리는 계획을 낼 수 있습니다. 무조건 되돌리기 전에 변경 의도가 맞는지 판단합니다.

**Import**는 이미 있는 객체를 Terraform 자원 주소와 연결하는 과정입니다. 기존 객체를 새로 만드는 명령이 아닙니다. Import 후 구성과 실제 값이 다르면 다음 plan에서 변경·교체가 나타날 수 있으므로 “import 성공 = 이관 완료”로 보지 않습니다. 해당 자원을 다른 도구도 동시에 관리하고 있다면 소유권을 정리해야 합니다. [Import 공식 문서](https://developer.hashicorp.com/terraform/language/import)

코드의 resource 이름만 바꾸면 Terraform이 기존 주소 삭제와 새 주소 생성을 계획할 수 있습니다. 같은 객체의 코드 주소를 옮기는 리팩터링에는 `moved` 블록 등을 검토합니다. state 파일을 텍스트 편집기로 직접 고치는 것은 일반적인 해결 방법이 아닙니다.

`lifecycle.prevent_destroy`는 삭제 계획을 차단하는 보호 장치지만 백업이 아니며, 구성에서 해당 resource 블록 자체를 제거한 경우까지 영구적으로 보호하는 장치도 아닙니다. 자원별 삭제 방지, 백업·복원 절차와 구분해야 합니다.

## 29. 두 도구를 연결하는 Terraform 실습

이 단계는 16절의 `lecture-local` 클러스터가 실행 중이어야 합니다. Terraform이 기존 클러스터 API에 접속해 **별도의 `lecture-tf` namespace**에 Deployment와 Service를 만듭니다. 클러스터 자체를 만드는 실습은 아닙니다.

앞선 YAML은 `lecture-demo`, 이 실습은 `lecture-tf`를 사용합니다. 같은 객체를 Terraform과 수동 YAML로 번갈아 바꾸지 않기 위해 구분했습니다. 조회·로그 확인에 `kubectl`을 쓰는 것은 괜찮습니다.

실행 파일: [terraform-kubernetes/main.tf](sample-files/kubernetes-terraform/terraform-kubernetes/main.tf)


```hcl
terraform {
  required_version = ">= 1.4, < 2.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.38.0"
    }
  }
}

variable "kubeconfig_path" {
  description = "로컬 kind 클러스터 전용 kubeconfig 경로"
  type        = string
  default     = "~/.kube/lecture-kind.yaml"
}

variable "replicas" {
  description = "실습 Deployment 복제본 수"
  type        = number
  default     = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 5 && floor(var.replicas) == var.replicas
    error_message = "replicas는 1부터 5 사이의 정수여야 합니다."
  }
}

provider "kubernetes" {
  config_path    = pathexpand(var.kubeconfig_path)
  config_context = "kind-lecture-local"
}

resource "kubernetes_namespace_v1" "lecture" {
  metadata {
    name = "lecture-tf"
  }
}

resource "kubernetes_deployment_v1" "web" {
  metadata {
    name      = "lecture-web"
    namespace = kubernetes_namespace_v1.lecture.metadata[0].name
  }

  spec {
    replicas = var.replicas
    selector {
      match_labels = { app = "lecture-tf-web" }
    }
    template {
      metadata {
        labels = { app = "lecture-tf-web" }
      }
      spec {
        container {
          name  = "nginx"
          image = "nginx:1.28.0-alpine"
          port {
            name           = "http"
            container_port = 80
          }
          resources {
            requests = { cpu = "100m", memory = "32Mi" }
            limits   = { cpu = "500m", memory = "128Mi" }
          }
          readiness_probe {
            http_get {
              path = "/"
              port = 80
            }
            period_seconds = 5
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "web" {
  metadata {
    name      = "lecture-web"
    namespace = kubernetes_namespace_v1.lecture.metadata[0].name
  }
  spec {
    selector = { app = "lecture-tf-web" }
    port {
      port        = 80
      target_port = 80
    }
    type = "ClusterIP"
  }
}

output "namespace" {
  value = kubernetes_namespace_v1.lecture.metadata[0].name
}
```


Provider는 전용 kubeconfig 파일과 `kind-lecture-local` context를 명시합니다. `~>` 제약은 이 예제에서 2.38.x 범위를 허용합니다. provider 버전은 학습 예제용 선택이며 최신 버전 추천을 뜻하지 않습니다. `.terraform.lock.hcl`이 생성되면 실제 선택 버전과 체크섬도 함께 관리합니다.

Namespace 이름을 문자열로 반복하는 대신 resource 속성을 참조하므로, Terraform은 Namespace가 Deployment·Service보다 먼저 필요함을 이해합니다. Service와 Pod를 연결하는 표식은 둘 다 `app = "lecture-tf-web"`입니다. 여기서는 기본 Nginx 페이지를 사용하므로 이전 YAML 실습과 화면 문구가 다른 것이 정상입니다.

예제 루트의 `terraform-kubernetes` 폴더로 이동해서 실행합니다. 앞선 실습 폴더에 있었다면 `cd ../terraform-kubernetes`입니다.

```sh
terraform init
terraform fmt -check
terraform validate
terraform plan -out=lesson.tfplan
terraform show lesson.tfplan
terraform apply lesson.tfplan
```

새 환경이라면 Namespace, Deployment, Service 총 3개의 생성이 예상됩니다. Provider 다운로드에는 인터넷 연결이 필요합니다. Kubernetes API에 접속되지 않으면 kubeconfig 경로, context, kind 상태부터 확인합니다.

```sh
export KUBECONFIG="$HOME/.kube/lecture-kind.yaml"
kubectl -n lecture-tf rollout status deployment/lecture-web --timeout=120s
kubectl -n lecture-tf get pods,services
kubectl -n lecture-tf port-forward service/lecture-web 8081:80
```

브라우저에서 `http://localhost:8081`을 열면 Nginx 기본 페이지가 보여야 합니다. Terraform은 객체를 만들었고 Kubernetes는 그 객체의 원하는 실행 상태를 유지합니다. Terraform이 매 순간 직접 컨테이너를 실행하는 것이 아닙니다.

복제본 변경 실습은 `terraform plan -var='replicas=3' -out=lesson.tfplan` 후 내용을 검토하고 apply합니다. HPA를 추가해 복제본 수를 자동 관리하려면 Terraform과 HPA가 같은 필드를 서로 되돌리지 않도록 관리 방식을 정해야 합니다.

## 30. 실습을 정리하는 순서

먼저 port-forward 터미널을 Ctrl+C로 종료합니다. 다음으로 Terraform이 만든 객체를 Terraform으로 지웁니다. **이 명령은 `terraform-kubernetes` 폴더에서 실행합니다.** 계획의 삭제 대상이 `lecture-tf` 실습 자원인지 확인하세요.

```sh
terraform plan -destroy -out=cleanup.tfplan
terraform show cleanup.tfplan
terraform apply cleanup.tfplan
```

그다음 YAML 실습 객체를 삭제합니다. 아래는 예제 루트에서 실행합니다.

```sh
export KUBECONFIG="$HOME/.kube/lecture-kind.yaml"
kubectl delete -f kubernetes/demo.yaml
kind delete cluster --name lecture-local --kubeconfig "$HOME/.kube/lecture-kind.yaml"
```

`lecture-demo` namespace를 지우면 그 안에 추가로 만든 객체도 함께 삭제될 수 있습니다. 실습 전용이라는 전제를 지켜야 합니다. Terraform 기초 실습의 기록도 없애려면 `terraform-basics`에서 `terraform destroy`를 수행합니다.

클러스터부터 없애면 Kubernetes provider가 객체를 삭제하려고 접속할 API도 없어집니다. 그래서 **클러스터 내부 객체 → 클러스터** 순서로 정리합니다. 이 순서는 실무에서도 의존 관계를 이해하는 데 도움이 됩니다.

## 31. 수강신청 서비스에 적용해 보기

기존 수강신청 프로젝트는 React, Spring Boot, PostgreSQL 같은 구성 요소를 생각하면 됩니다. Kubernetes로 옮기는 설계에서는 역할을 다음처럼 연결할 수 있습니다. 아래는 구조 설명이며 이 노트가 실제 프로젝트를 Kubernetes로 이관했다는 뜻은 아닙니다.

| 프로젝트 요소 | 연결되는 개념 | 설계할 것 |
| --- | --- | --- |
| Spring API 컨테이너 | Deployment | 이미지, 포트, 자원, 종료 처리 |
| API 접근 이름 | Service | label, targetPort |
| 공개 웹 주소 | 진입점·Ingress 또는 Gateway | DNS, TLS, 경로 |
| 일반 환경 설정 | ConfigMap | 환경별 분리, 갱신 방법 |
| DB 인증 정보 | Secret 또는 외부 비밀 관리 | 접근 권한, 주입, 회전 |
| 업로드 파일 | 객체 스토리지 또는 PVC | 백업, 접근 모드, 수명 |
| PostgreSQL | 관리형 DB 또는 별도 DB 운영 설계 | 백업, 장애조치, 연결 수 |
| 네트워크·클러스터 기반 | Terraform | 재현, 권한, 비용, state |

API Pod를 2개에서 10개로 늘리면 DB 연결 풀도 합산해서 증가할 수 있습니다. Pod당 최대 연결 수가 10이면 단순 계산상 최대 100개가 될 수 있습니다. DB 한도와 다른 작업의 연결도 함께 고려해야 합니다.

로그인 세션을 각 Pod 메모리에만 보관하면 다른 Pod로 요청이 갈 때 세션이 사라진 것처럼 보일 수 있습니다. 공유 세션 저장소나 인증 구조를 검토합니다. 강의 잔여석 차감은 DB 트랜잭션·잠금·제약을 통해 일관성을 유지해야 합니다. Kubernetes 복제본 확장이 중복 신청 문제를 해결해 주지는 않습니다.

AWS 배포 예제와 이어서 공부하려면 기존 [수강신청 AWS·Terraform 가이드](../projects/campus/AWS_TERRAFORM_GUIDE.html)를 참고하세요. 그 가이드의 ECS 배포와 Kubernetes 배포는 서로 다른 실행 플랫폼입니다.

## 32. CI/CD와 운영에서의 역할 분담

일반적인 흐름은 `소스 변경 → 테스트 → 이미지 빌드 → 이미지 저장소 업로드 → 배포 설정 변경 → 배포 확인`입니다. Terraform 기반 인프라 변경은 별도의 plan 검토 단계를 두는 경우가 많습니다.

Terraform으로 클러스터 기반을 관리하고 애플리케이션은 Helm 또는 GitOps 도구로 배포하는 방식도 있습니다. Helm은 Kubernetes 리소스 템플릿을 패키지로 관리하는 도구이고, GitOps는 Git에 기록한 선언과 실제 상태를 지속적으로 맞추는 운영 방식입니다. 여기서 중요한 것은 한 객체·한 필드의 관리 주체를 분명히 하는 것입니다.

운영 환경과 개발 환경은 변수 이름만 다르게 하는 것으로 충분하지 않을 수 있습니다. 계정·권한·클러스터·state 경계도 필요에 따라 분리합니다. Terraform workspace는 state를 구분하는 기능이지만 그 자체로 완전한 보안 격리를 보장하지 않습니다.

| 운영 질문 | 확인할 항목 |
| --- | --- |
| 누가 배포할 수 있나? | 클라우드 권한, Kubernetes RBAC, CI 권한 |
| 장애를 어떻게 알 수 있나? | 요청 성공률, 지연, 로그, 지표, 알림 |
| 업데이트를 되돌릴 수 있나? | 이전 이미지, 배포 이력, DB 호환성 |
| 데이터를 복원할 수 있나? | 백업뿐 아니라 실제 복원 연습 |
| 비용은 어디서 늘어나나? | 노드, 디스크, 로드밸런서, 로그, 네트워크 |

## 33. Terraform 오류를 읽는 순서

| 오류·상황 | 먼저 확인할 것 | 피할 행동 |
| --- | --- | --- |
| init에서 provider 다운로드 실패 | 네트워크, source, 버전 범위 | 무작정 버전을 전부 최신으로 바꾸기 |
| Unsupported argument | 선택한 provider 버전의 스키마 | 다른 버전 예제 그대로 복사 |
| Invalid value for variable | type·validation·입력값 | 검사 삭제로 문제 숨기기 |
| API 인증 실패 | 현재 계정·kubeconfig·context·권한 | 코드에 토큰 하드코딩 |
| Resource already exists | 같은 객체 존재, state 연결 여부 | 기존 객체부터 삭제 |
| State lock 오류 | 다른 작업 실행 중인지, 잠금 소유자 | 확인 없이 force-unlock |
| Saved plan is stale | state가 바뀌었는지 | 예전 계획을 강제 재사용 |
| 일부 apply 실패 | 완료된 자원과 실패 원인, 다시 plan | 전체가 자동 롤백됐다고 가정 |
| 예상하지 못한 교체 | 주소 변경·provider 속성·plan 이유 | `-auto-approve`로 넘어가기 |

`terraform state list`는 관리 중인 주소를, `terraform state show 주소`는 저장된 속성을 확인할 때 사용합니다. 출력에는 민감 정보가 있을 수 있으므로 그대로 공개 게시하지 않습니다. 상태 확인과 실제 앱 요청 확인을 모두 해야 배포 결과를 판단할 수 있습니다.

## 34. 자주 헷갈리는 질문 12개

**1. Docker를 배우면 Kubernetes를 쓸 필요가 없나요?** 이미지 제작·로컬 실행과 여러 노드의 운영은 다른 문제입니다. 작은 앱에는 Kubernetes의 운영 복잡성이 불필요할 수도 있습니다.

**2. Terraform과 Kubernetes 중 하나만 골라야 하나요?** 함께 사용할 수 있습니다. 기반 자원과 앱 실행 관리의 책임을 나누면 됩니다.

**3. Pod가 Running이면 배포 성공인가요?** Readiness, Service 연결, 실제 업무 요청도 확인해야 합니다.

**4. Service를 만들면 인터넷에서 바로 접속되나요?** 기본 ClusterIP는 내부용입니다. 외부 진입점과 네트워크 설정이 필요합니다.

**5. replicas를 늘리면 항상 빨라지나요?** DB·외부 API·네트워크가 병목이면 효과가 작거나 연결 부하가 커질 수 있습니다.

**6. Secret이면 Git에 올려도 되나요?** 실제 비밀값은 올리지 않습니다. base64는 쉽게 되돌릴 수 있습니다.

**7. plan을 하면 서버가 만들어지나요?** 계획된 자원 변경은 apply에서 수행합니다. plan에는 실제 상태 조회가 포함될 수 있습니다.

**8. apply를 두 번 하면 자원이 두 배가 되나요?** 같은 구성·같은 state에서 일반적으로 두 번째 계획은 변경 없음입니다. state, 자원 주소, 외부 상태가 달라지면 결과도 달라집니다.

**9. state가 오류를 내면 지우면 되나요?** 연결 기록을 잃을 수 있습니다. 원인 확인과 복구 절차가 먼저입니다.

**10. Terraform 코드 파일 이름이 실행 순서인가요?** 같은 모듈 안에서는 참조 관계가 의존성을 결정합니다.

**11. 롤백하면 DB도 이전으로 돌아가나요?** 배포 템플릿 복원과 데이터 복원은 다릅니다.

**12. Kubernetes가 죽은 서버를 무조건 새로 만드나요?** Pod 운영과 노드 프로비저닝은 구분됩니다. 노드 확장·교체는 인프라 또는 별도 자동화에 의존합니다.

## 35. 복습 문제와 학습 순서

처음에는 1~15절로 개념을 읽고, 16~19절에서 Kubernetes를 실행한 뒤, 20~28절에서 Terraform을 배우세요. 마지막에 29~30절로 두 기술을 연결하면 각각의 역할을 직접 확인할 수 있습니다.

| 학습 단계 | 해볼 일 | 스스로 설명할 수 있어야 하는 것 |
| --- | --- | --- |
| 1회차 | 이미지·컨테이너·Pod 그림 그리기 | 세 개념의 차이 |
| 2회차 | YAML 배포와 접속 | Deployment와 Service의 관계 |
| 3회차 | Pod 삭제·복제본 변경 | 누가 새 Pod를 만드는가 |
| 4회차 | Terraform 기초 예제 | 구성·실제 객체·state의 차이 |
| 5회차 | Terraform Kubernetes 배포 | 두 도구의 역할 경계 |
| 6회차 | 일부러 잘못된 값 입력 후 복구 | 로그와 plan을 읽는 방법 |

<details><summary>문제 1. Pod IP가 바뀌어도 같은 이름으로 접근하게 해 주는 것은?</summary><p>일반적으로 Service입니다. Service의 selector와 Pod label이 일치해야 대상이 연결됩니다.</p></details>

<details><summary>문제 2. readinessProbe가 실패하면 곧바로 컨테이너가 재시작되나요?</summary><p>아닙니다. Readiness는 트래픽 수신 준비 상태를 나타냅니다. 재시작은 liveness/startup 실패나 프로세스 종료 등 다른 조건과 연결됩니다.</p></details>

<details><summary>문제 3. replicas 3인데 Pod 두 개가 Pending이면 무엇을 보나요?</summary><p>describe와 이벤트에서 자원 부족, 스케줄링 조건, 저장소 조건 등을 봅니다. replicas를 더 늘리는 것으로 해결된다고 가정하지 않습니다.</p></details>

<details><summary>문제 4. terraform_data의 replicas를 3으로 바꾸면 Pod가 세 개 생기나요?</summary><p>아닙니다. 첫 실습은 내장 자원에 학습 데이터를 저장합니다. 실제 Pod 수를 변경하려면 Kubernetes Deployment 같은 해당 자원을 관리해야 합니다.</p></details>

<details><summary>문제 5. `.terraform.lock.hcl`과 state lock은 어떻게 다른가요?</summary><p>전자는 provider 의존성 버전·체크섬 기록이고, 후자는 동시 state 변경 충돌을 막기 위한 잠금입니다.</p></details>

<details><summary>문제 6. 저장한 plan을 apply하면 yes를 다시 입력하나요?</summary><p>일반적으로 아닙니다. 저장한 plan을 명시한 apply는 그 계획을 적용하므로 적용 전에 검토해야 합니다.</p></details>

<details><summary>문제 7. 클러스터와 클러스터 내부 Terraform 자원 중 무엇을 먼저 삭제하나요?</summary><p>내부 자원을 먼저 삭제합니다. 클러스터를 먼저 없애면 provider가 삭제를 요청할 API에 접속할 수 없습니다.</p></details>

<details><summary>문제 8. 수강신청 API를 10개로 늘리면 마지막 한 자리의 중복 신청이 자동 방지되나요?</summary><p>아닙니다. DB 트랜잭션, 잠금, 제약 등으로 업무 데이터의 일관성을 유지해야 합니다.</p></details>

## 36. 공식 자료와 검증 범위

이 문서의 설명은 2026-10-16에 공식 자료를 확인해 작성했습니다. 설치 방법과 지원 버전, provider 스키마는 사용 시점의 공식 문서도 확인하세요. 각 장의 관련 링크 외에 다음 자료로 이어서 학습할 수 있습니다.

- [Kubernetes 개념 전체](https://kubernetes.io/docs/concepts/)
- [kubectl 사용·설치 도구](https://kubernetes.io/docs/tasks/tools/)
- [kind 로컬 클러스터](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [Terraform CLI](https://developer.hashicorp.com/terraform/cli)
- [Kubernetes provider](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs)
- [기존 Terraform 상세 가이드](terraform-reference.html)
- [기존 Docker 사용법](docker-reference.html)

검증 완료: Terraform 1.16.5에서 두 예제의 `fmt -check`와 `validate`를 통과했습니다. 기초 실습은 실제 plan·apply, 재실행 시 변경 없음, replicas 변경, 잘못된 입력 거부, destroy까지 확인했습니다. Kubernetes provider 2.38.0을 사용했으며 macOS ARM64·Linux AMD64·Windows AMD64의 체크섬을 잠금 파일에 기록했습니다.

Kubernetes YAML의 구조와 label·selector·포트·ConfigMap 참조를 검사했습니다. 로컬 Docker 데몬 연결이 유지되지 않아 Kubernetes 클러스터에서의 실제 배포·접속과 Terraform Kubernetes plan/apply는 실행 검증하지 못했습니다. 따라서 해당 단계의 화면과 동작 설명은 예상 결과입니다. HTML의 목차·문서 내부 링크·예제 다운로드 경로와 데스크톱/모바일 배치, 검색, 테마 전환, 복습 문제 펼치기를 확인했습니다. 실제 AWS 자원은 만들지 않았습니다.

예제에는 실제 계정 키나 비밀번호가 없습니다. 이 문서는 학습용 구성이며 운영 서비스의 권한·백업·고가용성 설계를 모두 구현한 배포 패키지는 아닙니다.
