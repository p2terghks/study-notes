# AWS 컴퓨팅 서비스 요약

## 전체 지도 — 무엇을 실행할까?

**컴퓨팅은 코드를 실행할 CPU·메모리·실행 환경을 제공하는 영역입니다.** 이 문서는 주요 서비스 중심이며 모든 AWS 서비스를 나열하지 않습니다. 공식 자료 확인일은 **2026-09-29**입니다. 사용 가능 리전·정책·요금은 변경될 수 있습니다.

| 서비스 | 한 줄 설명 | 대표 용도 |
|---|---|---|
| EC2 | 가상 서버 직접 운영 | 서버 설정을 직접 제어 |
| Lightsail | 간단한 서버 패키지 | 소규모 웹·블로그 |
| Lambda | 이벤트에 따라 함수 실행 | 파일 처리·짧은 API |
| ECS | 컨테이너 배치·유지 관리 | 컨테이너 웹·작업 |
| Fargate | 서버 관리 없는 컨테이너 실행 기반 | ECS/EKS 실행 용량 |
| EKS | 관리형 Kubernetes | Kubernetes 기반 운영 |
| Elastic Beanstalk | 앱 배포와 인프라 구성 자동화 | 플랫폼 기반 웹 앱 |
| Batch | 작업 큐·배치 실행 관리 | 대량 계산·변환 |
| ECS Express Mode | 웹 컨테이너 배포 간소화 | 이미지로 서비스 시작 |
| App Runner | 기존 고객용 관리형 웹 앱 서비스 | 기존 서비스 운영·이전 검토 |

**중요:** ECS와 EKS는 컨테이너를 관리하는 계층이고, EC2와 Fargate는 실행 자원 선택지입니다. 모두 같은 계층의 대체재는 아닙니다.

[공식 컴퓨팅 서비스 목록](https://aws.amazon.com/products/compute/)

## EC2 — 가상 서버

**기능:** OS, 인스턴스 사양, 네트워크와 실행 프로그램을 직접 제어합니다.

**사용할 때:** Spring JAR을 직접 운영하거나 특정 OS·에이전트·서버 설정이 필요할 때.

**시작 순서**

1. 리전 선택 → EC2 인스턴스 시작.
2. AMI(OS 이미지), 인스턴스 타입, 스토리지 선택.
3. IAM 역할, 서브넷, 보안 그룹, 접속 방법 설정.
4. 인스턴스 상태 검사 통과 후 SSM 또는 설정한 SSH로 접속.
5. JDK와 앱을 준비하고 실행 → 로그와 헬스 체크 확인.

```bash
# JDK와 app.jar가 준비된 서버에서 실행하는 예시
java -jar app.jar
```

| 내가 관리할 것 | 확인할 것 |
|---|---|
| OS·런타임 패치, 앱 실행 유지 | 재부팅 후 자동 시작 설정 |
| 보안 그룹·포트 | 서버가 외부 요청을 받을 주소에 바인딩되는지 |
| 저장소·백업 | 종료 때 볼륨 삭제 설정 |

기존 로컬 예제의 `server.address=127.0.0.1`은 외부 접속을 받지 않습니다. 배포 환경의 바인딩·보안 그룹·프록시 구성을 함께 맞춰야 합니다. 운영 실행은 터미널 한 번 실행 대신 서비스 관리자 등을 사용합니다.

[EC2 공식 시작 안내](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html)

## Lightsail — 간편한 서버 패키지

**기능:** 서버·스토리지·네트워크 구성을 비교적 단순한 흐름으로 제공합니다. 정액형 번들이 있지만 모든 초과 사용·연결 서비스가 무료라는 뜻은 아닙니다.

**사용할 때:** 개인 웹사이트, 소규모 앱, 간단한 가상 서버 운영.

**시작 순서**

1. Lightsail에서 위치와 인스턴스 이미지 선택.
2. OS 또는 WordPress 같은 앱 이미지 선택.
3. 번들 선택 → 인스턴스 생성.
4. 브라우저 SSH로 접속하거나 앱 화면 확인.
5. 필요하면 고정 IP·DNS·스냅샷 구성.

**완료 확인:** 앱 URL 접속과 서버 상태를 확인합니다. 단순한 생성 흐름이어도 OS·앱 보안 업데이트는 운영자의 역할이 남습니다. 복잡한 네트워크 요구가 생기면 EC2 구조도 비교하세요.

[Lightsail 공식 설명](https://aws.amazon.com/lightsail/)

## Lambda — 이벤트로 함수 실행

**기능:** 서버를 직접 마련하지 않고 요청·파일 업로드·메시지 등의 이벤트에 따라 함수를 실행합니다.

**사용할 때:** 업로드 후 썸네일 처리, 짧은 API, 자동화 작업. 실행 시간과 런타임 등의 제한이 있으므로 장시간 상주 프로세스와 구분합니다.

**시작 순서**

1. Lambda 함수 생성 → 지원 런타임과 실행 역할 선택.
2. 코드 작성·배포 → 테스트 이벤트 입력.
3. 반환값과 CloudWatch 로그 확인.
4. 필요할 때 API Gateway·S3·큐 등의 트리거 연결.
5. 시간 제한·메모리·동시성·실패 처리 설정.

```python
# lambda_function.py, 핸들러: lambda_function.lambda_handler

def lambda_handler(event, context):
    name = event.get("name", "방문자")
    return {"message": f"{name}님, 안녕하세요!"}
```

```json
{"name": "민수"}
```

이 코드는 콘솔 테스트용 반환 객체입니다. API Gateway와 연결할 때는 해당 통합의 HTTP 응답 형식에 맞춰야 합니다. 재시도가 발생할 수 있는 작업은 같은 이벤트를 다시 처리해도 문제가 없도록 설계합니다.

[Lambda 공식 시작 안내](https://docs.aws.amazon.com/lambda/latest/dg/getting-started.html)

## ECS — 컨테이너 서비스 관리

**기능:** 컨테이너를 어디에 몇 개 실행할지 관리하고 서비스를 유지합니다.

| 용어 | 의미 |
|---|---|
| Image | 실행할 앱을 포장한 이미지 |
| Task definition | 이미지·CPU·메모리·포트·역할 설정 |
| Task | 실행 중인 작업 단위 |
| Service | 원하는 수의 Task를 유지·교체 |
| Cluster | Task와 서비스의 논리적 묶음 |

**시작 순서**

1. 앱 이미지를 빌드하고 ECR 같은 레지스트리에 업로드.
2. Task definition에 이미지·포트·로그·IAM 역할 설정.
3. Cluster와 실행 기반(Fargate/EC2 등) 구성.
4. 장기 실행 웹 앱이면 Service 생성.
5. 네트워크·헬스 체크·필요 시 ALB 연결.
6. Task가 정상 실행되는지, 로그와 앱 응답 확인.

Task execution role은 이미지 가져오기·로그 전송 등 실행 준비용이고, task role은 앱 코드의 AWS 접근 권한용입니다. 이미지가 있다고 자동으로 외부 웹 URL이 생기는 것은 아닙니다.

[Amazon ECS 공식 FAQ](https://aws.amazon.com/ecs/faqs/)

## Fargate — 컨테이너 실행 기반

**기능:** 컨테이너를 실행할 서버의 프로비저닝·패치를 직접 관리하지 않도록 합니다. 컨테이너 이미지 자체나 앱 버그를 대신 관리하지는 않습니다.

**사용할 때:** ECS/EKS로 컨테이너를 운영하면서 워커 서버 관리 부담을 줄이고 싶을 때.

```text
이미지 → ECS 서비스 또는 EKS Pod → Fargate 실행 환경
```

**사용 순서:** ECS Task를 Fargate 호환으로 정의하거나 EKS Fargate profile에서 대상 Pod를 선택 → CPU·메모리·네트워크·권한 설정 → 배포 → 로그와 실행 상태 확인.

| 줄어드는 관리 | 여전히 필요한 관리 |
|---|---|
| 호스트 OS와 서버 용량 마련 | 이미지 업데이트·앱 보안 |
| 컨테이너 실행 서버 운영 | Task/Pod 리소스·네트워크·권한 |

영구 데이터는 실행 중인 컨테이너의 임시 파일에만 의존하지 말고 적절한 저장소에 보관합니다. EKS에서의 지원 기능과 제약은 별도로 확인하세요.

[Fargate 시작 안내](https://aws.amazon.com/fargate/getting-started/) · [EKS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)

## EKS — 관리형 Kubernetes

**기능:** Kubernetes 컨트롤 플레인을 관리형으로 제공합니다. 앱·Pod·권한·네트워크와 실행 자원은 선택한 운영 방식에 맞게 구성합니다.

**사용할 때:** Kubernetes 생태계, 공통 배포 도구, 기존 Kubernetes 운영 경험이 필요할 때.

**시작 순서**

1. 클러스터 IAM 역할과 VPC·서브넷 준비.
2. EKS 클러스터 생성과 접근 권한 설정.
3. 노드 그룹 등 실행 용량 또는 Fargate profile 구성.
4. kubectl이 사용할 클러스터 접속 정보 설정.
5. Deployment·Service 등 매니페스트 적용.
6. Pod 상태·로그·Service·Ingress 경로 확인.

```bash
# 접속 권한과 kubeconfig가 준비된 뒤 상태를 확인하는 명령
kubectl get nodes
kubectl get pods -A
kubectl get services -A
```

클러스터가 생성됐다고 앱이 자동 배포되지는 않습니다. 기본 웹 하나만 올리는 목적이라면 ECS 등과 운영 복잡도를 비교하세요.

[EKS 공식 샘플 배포](https://docs.aws.amazon.com/eks/latest/userguide/sample-deployment.html)

## Elastic Beanstalk — 앱 배포 환경 관리

**기능:** 플랫폼에 맞는 앱을 배포하면 EC2, 로드 밸런싱, 확장, 상태 관리 구성을 도와줍니다. 인프라가 사라지는 서비스는 아닙니다.

**사용할 때:** 지원되는 플랫폼으로 웹 앱을 배포하며 개별 인프라 설정 부담을 줄이고 싶을 때.

**시작 순서**

1. Application과 Environment 생성.
2. 지원 플랫폼과 버전 선택.
3. 플랫폼 규칙에 맞는 소스 번들/JAR/컨테이너 설정 업로드.
4. 환경 변수·역할·네트워크·스케일링 설정.
5. 환경 URL·Health·로그 확인.

새 버전은 애플리케이션 버전으로 배포하고 상태를 점검합니다. 기반 EC2·로드 밸런서 등의 비용이 발생합니다. 종료할 때는 환경과 외부 DB 등 별도 자원을 구분하세요.

[Elastic Beanstalk 공식 설명](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/Welcome.html)

## AWS Batch — 대량 작업 실행

**기능:** Job을 큐에 넣고 실행 자원에 배치합니다. 실행할 코드나 컨테이너 이미지는 사용자가 준비합니다.

**사용할 때:** 대량 파일 변환, 시뮬레이션, 데이터 처리처럼 시작과 끝이 있는 작업.

| 용어 | 의미 |
|---|---|
| Compute environment | 작업 실행 자원 설정 |
| Job queue | 작업 대기열 |
| Job definition | 이미지·명령·리소스 요구 |
| Job | 제출한 실제 작업 |

**시작 순서:** 실행 환경 생성 → Job queue 연결 → Job definition 등록 → Job 제출 → 상태와 로그 확인.

재시도와 시간 제한을 설정하고 결과는 S3 같은 영구 저장소에 남깁니다. EC2/Fargate 등 선택한 자원에 따라 지원 조건이 달라집니다. 항상 떠 있어야 하는 웹 서버와 목적이 다릅니다.

[Batch 공식 설명](https://docs.aws.amazon.com/batch/latest/userguide/what-is-batch.html)

## ECS Express Mode와 App Runner 변경 사항

### ECS Express Mode

**기능:** 컨테이너 이미지와 IAM 역할 등을 받아 ECS/Fargate 웹 서비스, 로드 밸런싱과 확장 구성을 간소화합니다.

**시작 순서:** ECS 콘솔에서 Express Mode 선택 → 이미지·Task execution role·Infrastructure role 입력 → 앱 포트와 헬스 체크 경로 설정 → 생성 → 제공된 엔드포인트와 로그 확인.

이미지를 먼저 준비해야 하며 기본 리소스 비용이 발생합니다. 기존 소스 기반 배포라면 이미지 빌드 과정도 필요합니다.

[ECS Express Mode 공식 시작 안내](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-first-run.html)

### App Runner

**변경 사항:** 2026-04-30부터 신규 고객을 받지 않습니다. 기존 고객은 계속 사용할 수 있고 새 리소스도 생성할 수 있지만 AWS는 새 기능 추가를 계획하지 않는다고 안내합니다.

기존 고객의 사용 흐름은 소스/이미지 연결 → 빌드·시작 설정 → 배포 → 서비스 URL·로그 확인입니다. 신규 도입 및 이전 검토 시 AWS가 안내하는 ECS Express Mode를 함께 확인하세요.

[App Runner 서비스 공지](https://aws.amazon.com/apprunner/) · [공식 가용성 변경·이전 안내](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html)

## 함께 사용하는 서비스 — ALB·Auto Scaling

| 기능 | 역할 | 사용 순서 |
|---|---|---|
| ALB | HTTP/HTTPS 요청 분산 | Target group → Listener → 경로·헬스 체크 |
| EC2 Auto Scaling | EC2 수량 유지·조절 | Launch template → ASG → 최소·희망·최대·정책 |
| CloudWatch | 로그·지표·경보 | 로그 수집 → 지표 확인 → 경보 |
| ECR | 컨테이너 이미지 저장 | Repository → 이미지 push → 배포에서 참조 |

ALB는 서버를 실행하지 않고 트래픽을 전달합니다. Auto Scaling은 서버 수량을 조절하고, 앱 데이터 공유와 세션 설계까지 자동 해결하지는 않습니다.

```text
사용자 → ALB → 여러 EC2 또는 컨테이너
                   ↓
              공통 DB·파일 저장소
```

[ALB 공식 설명](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) · [EC2 Auto Scaling 공식 설명](https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html)

## 상황별 선택과 비용 확인

아래는 서비스 특성을 기준으로 정리한 **학습용 선택 기준**입니다. 절대적인 정답이나 최저 비용 보장은 아닙니다.

| 상황 | 먼저 비교할 선택지 |
|---|---|
| OS부터 직접 학습 | EC2 |
| 작은 웹을 간단히 운영 | Lightsail |
| 이미지로 웹 앱 배포 | ECS + Fargate / ECS Express Mode |
| 이벤트 기반 짧은 작업 | Lambda |
| Kubernetes 운영 필요 | EKS |
| 플랫폼 기반 앱 배포 | Elastic Beanstalk |
| 끝이 있는 대량 작업 | Batch |
| React 정적 빌드 결과 배포 | S3·CloudFront 또는 Amplify Hosting 검토 |

React의 정적 파일 호스팅과 Spring의 서버 실행은 서로 다른 요구입니다. SSR 서버가 필요한 React 프레임워크는 별도의 실행 환경을 고려합니다.

**시작 전에 볼 것:** 리전 지원, IAM 역할, 네트워크, 예상 사용량, 예산 알림. **학습 후 볼 것:** 서버뿐 아니라 디스크·로드 밸런서·NAT·IP·로그 등 남은 자원. 정지와 삭제는 다르며 정지해도 저장소 등 비용이 남을 수 있습니다.

이 문서의 AWS 생성 절차는 학습 설명입니다. 실제 계정에서 리소스를 만들거나 배포하지 않았습니다. 가격 수치를 고정하지 않았으므로 [AWS 요금 계산기](https://calculator.aws/)와 각 서비스 요금 페이지에서 본인 구성으로 확인하세요.
