# Article 4. MCP 연동 및 K3s 확장

## 1. 작업 목표

Article 4에서는 기존 학원 학생 관리 시스템의 Service 계층을 MCP Tool로 연결하고, Docker 이미지로 만든 애플리케이션을 K3s 환경에 배포한다.

구현 범위는 다음과 같다.

- Python MCP SDK 설치
- MCP 서버 구성
- 대시보드 조회 MCP Tool 구현
- 학생 상세 조회 MCP Tool 구현
- MCP Client를 이용한 Tool 목록 조회 및 실행 테스트
- 기존 Service 및 MySQL 데이터와 MCP 연결 확인
- Docker 이미지를 K3s에서 사용할 수 있도록 import
- K3s Deployment 구성
- K3s NodePort Service 구성
- K3s Pod 실행 확인
- K3s 환경에서 MySQL 연결 확인
- Windows 브라우저에서 K3s 서비스 접속 확인


---

## 2. MCP 설치

Windows 개발환경의 Python 가상환경 `.venv`에서 MCP SDK를 설치하였다.

```powershell
pip install "mcp[cli]"
```

설치 후 버전을 확인하였다.

```powershell
pip show mcp
```

확인 결과:

```text
Name: mcp
Version: 2.3.0
Summary: Model Context Protocol SDK
```

따라서 프로젝트에서는 MCP 2.3.0을 사용하였다.


---

## 3. MCP 서버 구성

MCP 기능을 별도의 파일로 분리하기 위해 다음 파일을 생성하였다.

```text
app/
└─ mcp_server.py
```

기존 FastAPI의 Service 계층을 MCP에서도 그대로 사용하도록 구성하였다.

이를 통해 MCP를 위해 학생 데이터 조회 로직을 새로 작성하지 않고 기존 애플리케이션 로직을 재사용하였다.


---

## 4. 대시보드 조회 MCP Tool 구현

첫 번째 MCP Tool로 학원 전체 운영 현황을 조회하는 `get_dashboard`를 구현하였다.

사용한 기존 Service 함수:

```text
get_dashboard_summary()
```

MCP Tool:

```python
@mcp.tool()
def get_dashboard() -> dict[str, int]:
    """학원의 학생 수, 오늘 출결, 이번 달 수납 현황을 조회한다."""
    with SessionLocal() as session:
        return get_dashboard_summary(session)
```

이 Tool은 다음 정보를 반환한다.

- 전체 학생 수
- 중1반 학생 수
- 중2반 학생 수
- 중3반 학생 수
- 오늘 출석 수
- 오늘 지각 수
- 오늘 결석 수
- 이번 달 납부 수
- 이번 달 미납 수


---

## 5. MCP 서버 실행

MCP 서버는 FastAPI 개발 서버와 충돌하지 않도록 8001번 포트를 사용하였다.

실행 코드:

```python
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
    )
```

Windows 터미널에서 실행하였다.

```powershell
py -m app.mcp_server
```

실행 결과:

```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO     StreamableHTTP session manager started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8001
```

MCP 서버가 정상적으로 실행되는 것을 확인하였다.


---

## 6. MCP Client 테스트

MCP Tool을 직접 호출하기 위해 프로젝트 최상위에 테스트용 클라이언트를 작성하였다.

```text
test_mcp_client.py
```

클라이언트에서는 다음 작업을 수행하였다.

1. MCP 서버 연결
2. MCP Tool 목록 조회
3. `get_dashboard` Tool 호출
4. 반환 데이터 확인


---

## 7. MCP 테스트 중 발생한 문제 - 가상환경 미활성화

### 문제 상황

MCP 서버를 실행한 터미널과 별도로 새 PowerShell 터미널을 열고 다음 명령을 실행하였다.

```powershell
py test_mcp_client.py
```

다음 오류가 발생하였다.

```text
ModuleNotFoundError: No module named 'mcp'
```


### 원인

MCP 패키지는 프로젝트의 `.venv` 가상환경에 설치되어 있었지만 새로 연 PowerShell 터미널에서는 가상환경이 활성화되어 있지 않았다.


### 해결

새 PowerShell 터미널에서 가상환경을 활성화하였다.

```powershell
.\.venv\Scripts\Activate.ps1
```

정상 활성화 후 프롬프트:

```text
(.venv) PS D:\OneDrive\#classes\October\1008\classwork\academy-student-manager>
```

이후 다시 실행하였다.

```powershell
py test_mcp_client.py
```

MCP 패키지를 정상적으로 인식하였다.


---

## 8. 대시보드 Tool 호출 확인

MCP Client에서 Tool 목록을 조회하였다.

결과:

```text
=== MCP Tools ===
get_dashboard
```

`get_dashboard` Tool 호출 결과:

```text
{
    'total_students': 60,
    'grade_1_students': 20,
    'grade_2_students': 20,
    'grade_3_students': 20,
    'today_present': 48,
    'today_late': 8,
    'today_absent': 4,
    'monthly_paid': 55,
    'monthly_unpaid': 5
}
```

결과 상태:

```text
is_error: False
```

이를 통해 다음 흐름이 정상 동작함을 확인하였다.

```text
MCP Client
↓
MCP Server
↓
get_dashboard Tool
↓
Service
↓
SQLAlchemy
↓
MySQL
```


---

## 9. 학생 상세 조회 MCP Tool 구현

두 번째 MCP Tool로 학생 ID를 이용한 학생 상세 조회 기능을 구현하였다.

기존 Service 함수:

```text
get_student_detail()
```

기존 Pydantic Response Model:

```text
StudentDetailResponse
```

MCP Tool에서는 Service 결과를 `StudentDetailResponse`로 검증한 뒤 JSON 형태로 반환하도록 구성하였다.

```python
@mcp.tool()
def get_student_detail(student_id: int) -> dict[str, object]:
    """학생 ID로 학생 기본정보, 최근 출결, 이번 달 수납 정보를 조회한다."""
    with SessionLocal() as session:
        try:
            result = get_student_detail_service(
                session=session,
                student_id=student_id,
            )
        except LookupError as error:
            return {
                "error": str(error),
            }

        response = StudentDetailResponse.model_validate(result)

        return response.model_dump(mode="json")
```


---

## 10. MCP 서버 최종 구성

`app/mcp_server.py`에는 다음 두 Tool을 등록하였다.

```text
get_dashboard
get_student_detail
```

두 Tool은 각각 별도의 데이터 접근 코드를 새로 작성하지 않고 기존 Service 계층을 호출한다.

구조:

```text
MCP Tool
↓
Service
↓
Repository
↓
SQLAlchemy
↓
MySQL
```

이를 통해 Web API와 MCP가 동일한 비즈니스 로직과 데이터를 사용하도록 구성하였다.


---

## 11. 학생 상세 조회 MCP 테스트

MCP Client에서 다시 Tool 목록을 확인하였다.

결과:

```text
=== MCP Tools ===
get_dashboard
get_student_detail
```

1번 학생을 대상으로 다음 Tool을 호출하였다.

```text
get_student_detail
student_id = 1
```

실제 반환 결과:

```text
{
    'student': {
        'student_id': 1,
        'name': '김민준',
        'grade': 1,
        'school': '한빛중학교',
        'guardian_phone': '010-1001-2001',
        'status': '재원',
        'class_id': 1
    },
    'recent_attendance': [
        {
            'attendance_id': 1,
            'student_id': 1,
            'attendance_date': '2026-10-08',
            'status': '출석',
            'note': None
        },
        {
            'attendance_id': 61,
            'student_id': 1,
            'attendance_date': '2026-10-07',
            'status': '출석',
            'note': None
        },
        {
            'attendance_id': 121,
            'student_id': 1,
            'attendance_date': '2026-10-06',
            'status': '출석',
            'note': None
        }
    ],
    'current_payment': {
        'payment_id': 1,
        'student_id': 1,
        'billing_month': '2026-10',
        'amount': 300000,
        'status': '납부',
        'paid_at': '2026-10-08'
    }
}
```

결과 상태:

```text
is_error: False
```

따라서 MCP를 통해 다음 정보를 정상 조회할 수 있음을 확인하였다.

- 학생 기본정보
- 최근 출결 3건
- 현재 월 수납 정보


---

## 12. MCP 최종 확인

MCP 구현 결과:

- [x] MCP SDK 설치
- [x] MCP 서버 실행
- [x] `get_dashboard` Tool 구현
- [x] `get_student_detail` Tool 구현
- [x] MCP Tool 목록 조회
- [x] MCP Tool 실행
- [x] 실제 MySQL 데이터 반환 확인
- [x] 기존 Service 계층 재사용 확인

MCP 구현 후 데이터 흐름:

```text
MCP Client
        │
        ▼
MCP Server
        │
        ├─ get_dashboard
        │
        └─ get_student_detail
                │
                ▼
             Service
                │
                ▼
            Repository
                │
                ▼
            SQLAlchemy
                │
                ▼
              MySQL
```


---

## 13. K3s 상태 확인

MCP 구현을 완료한 후 기존 Multipass VM에 설치되어 있던 K3s를 이용하여 애플리케이션을 배포하였다.

K3s 노드 상태 확인:

```bash
kubectl get nodes
```

결과:

```text
NAME      STATUS   ROLES           AGE   VERSION
k3s-lab   Ready    control-plane   7d    v1.36.4+k3s1
```

노드 상태가 다음과 같이 확인되었다.

```text
Ready
```

따라서 K3s 클러스터를 사용할 수 있는 상태였다.


---

## 14. 기존 Pod 상태 확인

다음 명령으로 기존 K3s 리소스를 확인하였다.

```bash
kubectl get pods -A
```

기존 수업 실습에서 생성한 Web, 모니터링 등의 Pod가 남아 있었다.

이번 프로젝트와 직접 관련되지 않은 기존 리소스는 삭제하거나 수정하지 않고 그대로 유지하였다.


---

## 15. Docker 이미지와 K3s 이미지 저장소

Article 3에서 만든 Docker 이미지:

```text
academy-student-manager:1.0
```

이 이미지는 Docker가 관리하는 이미지이므로 K3s가 사용하는 containerd에서 바로 사용할 수 있도록 import 작업을 수행하였다.


---

## 16. Docker 이미지를 K3s로 Import

Docker 이미지를 파일로 따로 저장한 뒤 다시 불러오는 과정을 한 명령으로 연결하였다.

```bash
docker save academy-student-manager:1.0 | sudo k3s ctr images import -
```

결과:

```text
application/vnd.oci.image.manifest.v1+json
sha256:510e7af17c20c7004177f928de35d21eb3e2794212840d44026dcb658a544e75
```

Import 후 K3s 이미지 목록을 확인하였다.

```bash
sudo k3s ctr images list | grep academy-student-manager
```

결과:

```text
docker.io/library/academy-student-manager:1.0
```

따라서 Docker에서 만든 프로젝트 이미지가 K3s containerd에 정상 등록되었다.


---

## 17. 기존 Service와 NodePort 확인

새로운 NodePort Service를 만들기 전에 기존 서비스가 사용하는 포트를 확인하였다.

```bash
kubectl get svc -A
```

기존 NodePort 예:

```text
hello-service           30689
product-app-service     32301
monitoring-grafana      30300
traefik                 31003 / 30200
```

프로젝트에서는 기존 서비스와 충돌하지 않는 다음 포트를 사용하였다.

```text
30080
```


---

## 18. K3s Deployment 및 Service 작성

프로젝트 디렉터리에 다음 파일을 생성하였다.

```text
k8s.yaml
```

파일에는 Deployment와 Service를 함께 작성하였다.


### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: academy-student-manager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: academy-student-manager
  template:
    metadata:
      labels:
        app: academy-student-manager
    spec:
      containers:
        - name: academy-student-manager
          image: academy-student-manager:1.0
          imagePullPolicy: Never
          ports:
            - containerPort: 8000
          env:
            - name: DB_HOST
              value: "172.24.214.37"
            - name: DB_PORT
              value: "3306"
            - name: DB_NAME
              value: "academy_student_db"
            - name: DB_USER
              value: "academy_user"
            - name: DB_PASSWORD
              value: "academy_pw_2026"
```

`replicas`는 다음과 같이 설정하였다.

```text
1
```

이번 프로젝트에서는 K3s 동작 확인이 목적이므로 Pod 1개를 사용하였다.


### imagePullPolicy

다음과 같이 지정하였다.

```yaml
imagePullPolicy: Never
```

프로젝트 이미지를 외부 Registry에서 다운로드하는 것이 아니라 앞 단계에서 K3s containerd에 직접 import했기 때문이다.


---

## 19. NodePort Service 구성

같은 `k8s.yaml`에 Service를 작성하였다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: academy-student-manager-service
spec:
  type: NodePort
  selector:
    app: academy-student-manager
  ports:
    - port: 8000
      targetPort: 8000
      nodePort: 30080
```

포트 구조:

```text
Windows Browser
↓
172.24.214.37:30080
↓
K3s NodePort Service
↓
Service Port 8000
↓
Pod Port 8000
↓
FastAPI
```


---

## 20. K3s 리소스 적용

작성한 YAML을 적용하였다.

```bash
kubectl apply -f k8s.yaml
```

결과:

```text
deployment.apps/academy-student-manager created
service/academy-student-manager-service created
```

Deployment와 Service가 정상 생성되었다.


---

## 21. Pod 상태 확인

다음 명령으로 Pod를 확인하였다.

```bash
kubectl get pods
```

프로젝트 Pod:

```text
academy-student-manager-dbdfbcdd7-jcrcq
```

상태:

```text
READY   1/1
STATUS  Running
RESTARTS 0
```

따라서 프로젝트 Pod가 정상 실행되었다.


---

## 22. Service 상태 확인

다음 명령으로 프로젝트 Service를 확인하였다.

```bash
kubectl get svc academy-student-manager-service
```

결과:

```text
NAME                              TYPE       CLUSTER-IP      PORT(S)
academy-student-manager-service   NodePort   10.43.168.31    8000:30080/TCP
```

따라서 다음 NodePort가 정상 생성되었다.

```text
30080
```


---

## 23. K3s에서 API 동작 확인

Multipass Ubuntu에서 NodePort를 통해 대시보드 API를 직접 호출하였다.

```bash
curl http://172.24.214.37:30080/api/dashboard
```

결과:

```json
{
    "total_students": 60,
    "grade_1_students": 20,
    "grade_2_students": 20,
    "grade_3_students": 20,
    "today_present": 48,
    "today_late": 8,
    "today_absent": 4,
    "monthly_paid": 55,
    "monthly_unpaid": 5
}
```

Article 3에서 Web 수납 테스트 후 변경된 최신 데이터인 다음 값도 정상 조회되었다.

```text
납부: 55
미납: 5
```

따라서 K3s Pod에서 실행 중인 FastAPI가 기존 MySQL과 정상 연결되어 있음을 확인하였다.


---

## 24. Windows 브라우저에서 K3s 서비스 확인

Windows 브라우저에서 다음 주소로 접속하였다.

```text
http://172.24.214.37:30080
```

다음 화면이 모두 정상적으로 표시되었다.

- 대시보드
- 학생
- 출결
- 수납

따라서 Windows에서 K3s NodePort를 통해 Pod 내부 FastAPI Web 애플리케이션에 정상 접근할 수 있음을 확인하였다.


---

## 25. Docker 실행과 K3s 실행 비교

Article 3에서는 Docker 컨테이너를 다음 주소로 실행하였다.

```text
http://172.24.214.37:8000
```

Article 4에서는 동일한 애플리케이션 이미지를 K3s에 배포하여 다음 주소로 실행하였다.

```text
http://172.24.214.37:30080
```

두 실행 구조를 비교하면 다음과 같다.


### Docker

```text
Windows Browser
↓
Multipass :8000
↓
Docker Container
↓
FastAPI
↓
MySQL
```


### K3s

```text
Windows Browser
↓
Multipass :30080
↓
K3s NodePort Service
↓
Deployment
↓
Pod
↓
FastAPI
↓
MySQL
```

동일한 FastAPI 애플리케이션을 Docker 이미지로 만든 뒤 K3s 환경으로 확장하여 실행하였다.


---

## 26. Article 4 완료 시 전체 시스템 구조

Article 4 완료 후 프로젝트는 Web API, Web UI, Docker, MCP, K3s까지 연결된 구조가 되었다.

```text
                         ┌─────────────────────┐
                         │   Windows Browser   │
                         └──────────┬──────────┘
                                    │
                          NodePort :30080
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     K3s Service     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Deployment       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │        Pod          │
                         │ FastAPI + Web UI    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │        MySQL        │
                         │ academy_student_db  │
                         └─────────────────────┘
```

MCP는 기존 애플리케이션의 Service 계층과 다음과 같이 연결하였다.

```text
MCP Client
↓
MCP Server
├─ get_dashboard
└─ get_student_detail
↓
Service
↓
Repository
↓
SQLAlchemy
↓
MySQL
```

Web API와 MCP가 각각 별도의 데이터 처리 로직을 만드는 것이 아니라 동일한 Service와 Repository를 사용한다.


---

## 27. 프로젝트 전체 Article 구성

최종 Article 구성은 다음과 같다.

### Article 1. 개발 기반 및 데이터베이스 구축

- 개발환경 구성
- MySQL 구성
- DB 연결
- 데이터 모델
- 초기 데이터
- Pydantic 기본 검증


### Article 2. 백엔드 핵심 기능 및 API 구현

- Schema
- Repository
- Service
- FastAPI API
- 학생 조회
- 출결
- 수납
- 대시보드


### Article 3. Web 화면 및 Docker 실행환경 구축

- Web UI
- JavaScript API 연동
- 대시보드
- 학생 관리
- 출결 관리
- 수납 관리
- Docker 이미지
- Docker 컨테이너


### Article 4. MCP 연동 및 K3s 확장

- MCP 서버
- MCP Tool
- MCP Client 테스트
- K3s 이미지 import
- Deployment
- Service
- NodePort
- Pod 실행
- Windows 브라우저 접속


---

## 28. 기능명세서와 최종 구현 비교

초기 기능명세서에서 정의한 핵심 기능은 Article 3까지 모두 구현하였으며 Article 4에서는 해당 기능을 MCP와 K3s 환경으로 확장하였다.

| 기능 ID | 기능 | 최종 상태 |
|---|---|---|
| DASHBOARD-001 | 운영 현황 조회 | 완료 |
| STUDENT-001 | 전체 학생 조회 | 완료 |
| STUDENT-002 | 학생 상세 조회 | 완료 |
| STUDENT-003 | 반별 학생 조회 | 완료 |
| ATTENDANCE-001 | 출결 조회 | 완료 |
| ATTENDANCE-002 | 출결 기록 | 완료 |
| PAYMENT-001 | 월별 수납 현황 조회 | 완료 |
| PAYMENT-002 | 납부 상태 처리 | 완료 |

추가 확장:

| 구분 | 구현 내용 | 상태 |
|---|---|---|
| MCP | 대시보드 조회 Tool | 완료 |
| MCP | 학생 상세 조회 Tool | 완료 |
| Docker | FastAPI 컨테이너 실행 | 완료 |
| K3s | Docker 이미지 import | 완료 |
| K3s | Deployment | 완료 |
| K3s | NodePort Service | 완료 |
| K3s | Web 서비스 접속 | 완료 |


---

## 29. Article 4 최종 체크리스트

### MCP

- [x] MCP SDK 설치
- [x] MCP 2.3.0 확인
- [x] MCP 서버 구성
- [x] Streamable HTTP 방식 실행
- [x] `get_dashboard` Tool 구현
- [x] `get_student_detail` Tool 구현
- [x] MCP Client 작성
- [x] Tool 목록 조회
- [x] 대시보드 데이터 조회
- [x] 학생 상세 데이터 조회
- [x] MySQL 최신 데이터 반환 확인
- [x] 기존 Service 재사용


### K3s

- [x] K3s 노드 `Ready` 확인
- [x] Docker 이미지 K3s containerd import
- [x] K3s 이미지 등록 확인
- [x] 기존 NodePort 사용 현황 확인
- [x] `k8s.yaml` 작성
- [x] Deployment 생성
- [x] Service 생성
- [x] NodePort `30080` 설정
- [x] Pod `1/1 Running` 확인
- [x] K3s API 호출 확인
- [x] K3s Pod → MySQL 연결 확인
- [x] Windows 브라우저에서 K3s Web 서비스 확인


---

## 30. Article 4 결과

Article 4에서는 기존 학생 관리 시스템의 기능을 MCP Tool로 연결하였다.

MCP를 위해 별도의 학생 관리 로직을 새로 만드는 대신 기존 Service 계층을 재사용하여 다음 기능을 Tool 형태로 제공하였다.

```text
get_dashboard
get_student_detail
```

MCP Client를 통해 실제 Tool 목록을 조회하고 Tool을 호출하여 MySQL의 데이터를 정상적으로 반환받는 것을 확인하였다.

또한 Article 3에서 생성한 Docker 이미지 `academy-student-manager:1.0`을 K3s containerd로 import하고 Deployment와 NodePort Service를 구성하였다.

최종적으로 다음 주소를 통해 Windows 브라우저에서 K3s에 배포된 애플리케이션에 접근하였다.

```text
http://172.24.214.37:30080
```

대시보드, 학생, 출결, 수납 화면이 모두 정상 동작하였으며 K3s Pod 내부의 FastAPI가 MySQL의 최신 데이터를 정상적으로 조회하는 것도 확인하였다.

이로써 다음 전체 흐름을 구현하고 검증하였다.

```text
Web UI
↓
FastAPI API
↓
Service
↓
Repository
↓
SQLAlchemy
↓
MySQL
```

```text
MCP Client
↓
MCP Tool
↓
Service
↓
Repository
↓
SQLAlchemy
↓
MySQL
```

```text
Windows Browser
↓
K3s NodePort
↓
Service
↓
Deployment
↓
Pod
↓
FastAPI
↓
MySQL
```

Article 1부터 Article 4까지 계획한 개발, 데이터베이스, API, Web, Docker, MCP, K3s 작업을 모두 완료하였다.