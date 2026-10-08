# Article 3. Web 화면 및 Docker 실행환경 구축

## 1. 작업 목표

Article 3에서는 Article 2에서 구현한 FastAPI API를 실제 사용자가 사용할 수 있도록 Web 화면과 연결하고, 완성된 애플리케이션을 Docker 이미지로 빌드하여 Multipass 환경에서 실행한다.

구현 범위는 다음과 같다.

- 대시보드 화면 구현
- 학생 목록 및 상세 조회 화면 구현
- 출결 조회 및 등록 화면 구현
- 수납 조회 및 납부 처리 화면 구현
- Web 화면과 FastAPI API 연동
- Docker 이미지 생성
- Docker 컨테이너 실행
- Docker 컨테이너에서 MySQL 연결 확인
- Windows 브라우저에서 Docker 서비스 접속 확인


---

## 2. Web 파일 구성

정적 Web 파일은 FastAPI 프로젝트 내부의 다음 경로에 구성하였다.

```text
app/
└─ static/
   ├─ index.html
   ├─ style.css
   └─ app.js
```

각 파일의 역할은 다음과 같다.

| 파일 | 역할 |
|---|---|
| `index.html` | 화면 구조 구성 |
| `style.css` | 화면 디자인 |
| `app.js` | FastAPI API 호출 및 화면 동작 처리 |


---

## 3. FastAPI와 Web 화면 연결

FastAPI에서 `app/static` 디렉터리를 정적 파일 경로로 등록하였다.

```python
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)
```

루트 경로 `/`에 접속하면 `index.html`을 반환하도록 구성하였다.

```python
@app.get("/", include_in_schema=False)
def read_index() -> FileResponse:
    return FileResponse("app/static/index.html")
```

Windows 개발 환경에서는 다음 명령으로 FastAPI를 실행하였다.

```powershell
uvicorn app.main:app --reload
```

접속 주소:

```text
http://127.0.0.1:8000
```

또는

```text
http://localhost:8000
```


---

## 4. 대시보드 구현

대시보드에서는 다음 API를 호출한다.

```text
GET /api/dashboard
```

화면에 표시하는 항목은 다음과 같다.

- 전체 학생 수
- 중1반 학생 수
- 중2반 학생 수
- 중3반 학생 수
- 오늘 출석 수
- 오늘 지각 수
- 오늘 결석 수
- 이번 달 납부 수
- 이번 달 미납 수

실제 테스트에서 다음과 같이 조회되었다.

```text
전체 학생: 60명

중1반: 20명
중2반: 20명
중3반: 20명

오늘 출석: 48명
오늘 지각: 8명
오늘 결석: 4명
```

수납 정보는 실제 납부 처리 결과가 바로 대시보드에 반영되는 것을 확인하였다.

테스트 과정의 예:

```text
납부 54 / 미납 6
↓
미납 학생 1명 납부 처리
↓
납부 55 / 미납 5
```

따라서 수납 처리 결과가 DB에 저장될 뿐 아니라 대시보드에서도 다시 조회되어 정상적으로 표시됨을 확인하였다.


---

## 5. 학생 관리 화면

### 5.1 학생 목록 조회

학생 화면에서는 전체 학생 60명을 조회할 수 있도록 구현하였다.

지원하는 조회 조건:

- 전체
- 중1반
- 중2반
- 중3반

각 반은 20명으로 구성되어 있다.

학생 목록에는 다음 정보를 표시한다.

- 학생 ID
- 이름
- 학년
- 학교
- 재원 상태

사용 API:

```text
GET /api/students
GET /api/students?class_id=1
GET /api/students?class_id=2
GET /api/students?class_id=3
```


### 5.2 학생 상세 조회

학생 목록에서 학생을 클릭하면 학생 상세 화면으로 전환되도록 구현하였다.

상세 화면에는 다음 정보를 표시한다.

- 이름
- 학년
- 학교
- 소속 반
- 보호자 연락처
- 최근 출결 기록
- 현재 월 수납 정보

사용 API:

```text
GET /api/students/{student_id}
```

상세 화면에는 `목록으로` 버튼을 두어 학생 목록 화면으로 돌아갈 수 있도록 구성하였다.


---

## 6. 출결 관리 화면

출결 화면에서는 날짜와 반을 선택하여 해당 학생들의 출결 현황을 조회할 수 있도록 구현하였다.

조회 조건:

- 날짜
- 반

표시 항목:

- 학생 ID
- 이름
- 학교
- 현재 출결 상태
- 출결 처리 버튼

사용 API:

```text
GET /api/classes/{class_id}/students
GET /api/attendance?date={date}&class_id={class_id}
```


### 6.1 출결 상태 표시

해당 날짜에 이미 출결 정보가 존재하면 다음 중 하나를 표시한다.

```text
출석
지각
결석
```

출결 정보가 없으면 다음과 같이 표시한다.

```text
미등록
```


### 6.2 출결 등록

출결이 아직 등록되지 않은 학생은 다음 버튼을 사용할 수 있도록 구현하였다.

```text
[출석] [지각] [결석]
```

버튼을 누르면 다음 API를 호출한다.

```text
POST /api/attendance
```

전송 데이터 예:

```json
{
    "student_id": 2,
    "attendance_date": "2026-10-01",
    "status": "출석",
    "note": null
}
```

등록이 성공하면 출결 목록을 다시 조회하고 대시보드도 다시 조회하도록 하였다.

따라서 출결 등록 후 화면과 대시보드에 변경 내용이 즉시 반영된다.


---

## 7. 수납 관리 화면

수납 화면에서는 월, 납부 상태, 반을 기준으로 수납 내역을 조회할 수 있도록 구현하였다.

조회 조건:

- 대상 월
- 상태
  - 전체
  - 납부
  - 미납
- 반
  - 전체
  - 중1반
  - 중2반
  - 중3반

표시 항목:

- 학생 ID
- 이름
- 학년
- 반
- 대상 월
- 수강료
- 납부 상태
- 납부일
- 처리 버튼

사용 API:

```text
GET /api/payments
GET /api/students
```

조건에 따라 다음과 같은 형태로 조회한다.

```text
GET /api/payments?month=2026-10
GET /api/payments?month=2026-10&status=미납
GET /api/payments?month=2026-10&class_id=1
GET /api/payments?month=2026-10&status=미납&class_id=1
```


### 7.1 학생 정보와 수납 정보 결합

수납 API에는 학생 이름이 직접 포함되어 있지 않으므로 Web에서 학생 목록도 함께 조회하였다.

학생 ID를 기준으로 학생 정보와 수납 정보를 연결하여 다음 정보를 화면에 표시하였다.

```text
학생 ID
이름
학년
반
수납 정보
```


### 7.2 납부 처리

미납 상태의 학생에게는 다음 버튼을 표시한다.

```text
[납부 처리]
```

납부 상태인 학생에게는 다음과 같이 비활성화된 버튼을 표시한다.

```text
[납부 완료]
```

미납 학생의 `납부 처리` 버튼을 누르면 다음 API를 호출한다.

```text
PATCH /api/payments/{payment_id}
```

정상 처리 시 다음 값이 변경된다.

```text
status: 미납 → 납부
paid_at: 처리한 날짜
```

테스트 결과 납부 처리 후 수납 목록이 즉시 갱신되었고, 대시보드의 납부/미납 숫자도 함께 변경되었다.


---

## 8. Web 기능 최종 확인

Web에서 다음 기능을 모두 확인하였다.

- [x] 대시보드 조회
- [x] 전체 학생 조회
- [x] 반별 학생 조회
- [x] 학생 상세 조회
- [x] 날짜별 출결 조회
- [x] 반별 출결 조회
- [x] 출결 등록
- [x] 월별 수납 조회
- [x] 납부/미납 상태별 조회
- [x] 반별 수납 조회
- [x] 미납 → 납부 처리
- [x] 출결 및 수납 변경 내용 대시보드 반영


---

## 9. Web 구현 중 발생한 문제 1 - Multipass IP 변경

### 문제 상황

Windows 컴퓨터를 재부팅한 뒤 Web 대시보드의 숫자가 모두 다음과 같이 표시되었다.

```text
-
```

브라우저에서 API를 직접 호출하였다.

```text
http://127.0.0.1:8000/api/dashboard
```

결과:

```text
Internal Server Error
```


### 원인 확인

Multipass 상태를 확인하였다.

```powershell
multipass list
```

기존 `.env`에 설정된 MySQL 주소는 다음과 같았다.

```text
172.19.251.109
```

재부팅 후 Multipass VM의 IP는 다음과 같이 변경되어 있었다.

```text
172.24.214.37
```

따라서 FastAPI가 존재하지 않는 기존 IP의 MySQL에 접속하려고 하면서 DB 연결 오류가 발생한 것이 원인이었다.


### 해결

`.env`의 `DB_HOST`만 현재 Multipass IP로 변경하였다.

변경 전:

```env
DB_HOST=172.19.251.109
```

변경 후:

```env
DB_HOST=172.24.214.37
```

Uvicorn을 다시 실행하였다.

```powershell
uvicorn app.main:app --reload
```

다시 API를 확인하였다.

```text
http://127.0.0.1:8000/api/dashboard
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
    "monthly_paid": 54,
    "monthly_unpaid": 6
}
```

MySQL 연결과 API가 정상 복구되었다.


---

## 10. Web 구현 중 발생한 문제 2 - HTML과 JavaScript 버전 불일치

### 문제 상황

`/api/dashboard` API는 정상적으로 데이터를 반환하고 있었지만 Web 대시보드의 숫자는 계속 `-`로 표시되었다.

브라우저 개발자 도구 Console에서 다음 오류를 확인하였다.

```text
Uncaught TypeError:
Cannot read properties of null (reading 'addEventListener')
```

또한 다음 오류도 발생하였다.

```text
Cannot read properties of null (reading 'classList')
```


### 원인

`app.js`에는 출결 화면 처리를 위한 다음 HTML 요소가 있다고 가정한 코드가 들어가 있었다.

```text
attendance-section
attendance-search-button
```

그러나 당시 실행 중이던 `index.html`은 이전 버전이었기 때문에 해당 요소가 존재하지 않았다.

그 결과:

```javascript
document.getElementById(...)
```

결과가 `null`이 되었고, JavaScript 실행이 중간에 중단되었다.

JavaScript가 끝까지 실행되지 않았기 때문에 마지막에 호출되는 `loadDashboard()` 역시 정상 동작하지 않았다.


### 해결

`index.html`과 `app.js`를 동일한 최신 화면 구조로 맞추었다.

브라우저에서 강력 새로고침을 실행하였다.

```text
Ctrl + F5
```

이후 다음 기능이 모두 정상 동작하였다.

- 대시보드 데이터 표시
- 학생 화면 전환
- 출결 화면 전환
- 출결 조회

참고로 개발자 도구에서 다음 오류도 확인되었으나 현재 기능과는 관계없는 favicon 요청이므로 별도 수정하지 않았다.

```text
/favicon.ico 404 (Not Found)
```


---

## 11. Docker 실행환경 구축

Web 구현을 완료한 후 애플리케이션을 Docker에서 실행하도록 구성하였다.

Docker는 Multipass VM `k3s-lab`에서 실행하였다.


### 11.1 Docker 설치 상태 확인

Multipass Ubuntu에 SSH로 접속하였다.

```powershell
ssh 1
```

Docker 버전 확인:

```bash
docker --version
```

결과:

```text
Docker version 29.1.3
```

Docker Compose 확인:

```bash
docker compose version
```

결과:

```text
Docker Compose version 2.40.3
```

Docker 실행 권한 확인:

```bash
docker ps
```

결과:

```text
CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
```

`permission denied` 오류 없이 정상 실행되는 것을 확인하였다.


---

## 12. Dockerfile 작성

프로젝트 최상위에 `Dockerfile`을 생성하였다.

프로젝트 구조:

```text
academy-student-manager/
├─ app/
├─ docs/
├─ .dockerignore
├─ .env
├─ Dockerfile
└─ requirements.txt
```

`Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

구성 내용:

1. Python 3.13 기반 이미지 사용
2. 컨테이너 작업 디렉터리를 `/app`으로 설정
3. `requirements.txt` 복사
4. Python 패키지 설치
5. 애플리케이션 코드 복사
6. FastAPI가 사용하는 8000번 포트 지정
7. Uvicorn을 `0.0.0.0:8000`으로 실행


---

## 13. `.dockerignore` 작성

Docker 이미지에 불필요한 파일이 포함되지 않도록 `.dockerignore`를 생성하였다.

```text
.venv
__pycache__
*.pyc
.git
docs
```

Windows 개발용 가상환경과 문서 등 Docker 실행에 필요하지 않은 파일은 이미지 생성 대상에서 제외하였다.


---

## 14. Windows 프로젝트를 Multipass로 전송

Ubuntu에 프로젝트 디렉터리를 생성하였다.

```bash
mkdir -p ~/academy-student-manager
```

Windows PowerShell에서 필요한 파일을 Multipass로 전송하였다.

```powershell
multipass transfer --recursive app k3s-lab:/home/ubuntu/academy-student-manager/
```

```powershell
multipass transfer requirements.txt Dockerfile .dockerignore .env k3s-lab:/home/ubuntu/academy-student-manager/
```

전송 후 Ubuntu에서 확인하였다.

```bash
cd ~/academy-student-manager
ls -la
```

확인된 파일:

```text
.dockerignore
.env
Dockerfile
app/
requirements.txt
```


---

## 15. Docker 이미지 빌드

Ubuntu의 프로젝트 디렉터리에서 다음 명령을 실행하였다.

```bash
docker build -t academy-student-manager:1.0 .
```

빌드 과정에서 다음 작업이 수행되었다.

- `python:3.13-slim` 이미지 다운로드
- `requirements.txt` 복사
- FastAPI, SQLAlchemy, PyMySQL 등 Python 패키지 설치
- `app` 소스코드 복사
- Uvicorn 실행 명령 설정

빌드 결과:

```text
Successfully built 510e7af17c20
Successfully tagged academy-student-manager:1.0
```

따라서 다음 Docker 이미지가 생성되었다.

```text
academy-student-manager:1.0
```


### 빌드 과정의 경고

다음 경고가 출력되었다.

```text
DEPRECATED: The legacy builder is deprecated
```

또한 Python 패키지 설치 시 다음 경고가 출력되었다.

```text
WARNING: Running pip as the 'root' user
```

두 메시지는 이번 이미지 빌드 실패를 의미하는 오류는 아니었으며 이미지 생성은 정상 완료되었다.


---

## 16. Docker 컨테이너 실행

다음 명령으로 컨테이너를 실행하였다.

```bash
docker run -d \
  --name academy-student-manager \
  --env-file .env \
  -p 8000:8000 \
  academy-student-manager:1.0
```

옵션의 의미:

| 옵션 | 의미 |
|---|---|
| `-d` | 백그라운드 실행 |
| `--name academy-student-manager` | 컨테이너 이름 지정 |
| `--env-file .env` | DB 연결 환경변수 전달 |
| `-p 8000:8000` | VM의 8000번 포트와 컨테이너 8000번 포트 연결 |
| `academy-student-manager:1.0` | 실행할 Docker 이미지 |

컨테이너 상태를 확인하였다.

```bash
docker ps
```

결과:

```text
CONTAINER ID   IMAGE                         STATUS       PORTS
43c9022787cc   academy-student-manager:1.0   Up           0.0.0.0:8000->8000/tcp
```

Docker 컨테이너가 정상 실행되는 것을 확인하였다.


---

## 17. Docker 컨테이너에서 MySQL 연결 확인

컨테이너가 단순히 실행되는 것만으로는 충분하지 않으므로 FastAPI가 실제 MySQL 데이터를 읽을 수 있는지 확인하였다.

Multipass Ubuntu에서 다음 명령을 실행하였다.

```bash
curl http://127.0.0.1:8000/api/dashboard
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

수납 Web 테스트에서 미납 학생을 추가로 납부 처리했기 때문에 이전의 `54 / 6`에서 다음과 같이 실제 DB 값이 변경되어 있었다.

```text
납부: 55
미납: 5
```

Docker 컨테이너에서도 변경된 최신 DB 값을 정상적으로 조회하였다.

따라서 다음 연결이 정상임을 확인하였다.

```text
Docker 컨테이너
    ↓
FastAPI
    ↓
SQLAlchemy + PyMySQL
    ↓
Multipass MySQL
    ↓
academy_student_db
```


---

## 18. Windows에서 Docker Web 서비스 접속 확인

Multipass의 현재 IP:

```text
172.24.214.37
```

Windows 브라우저에서 다음 주소로 접속하였다.

```text
http://172.24.214.37:8000
```

Docker 컨테이너에서 실행 중인 Web 화면이 정상적으로 표시되었다.

확인한 화면:

- 대시보드
- 학생
- 출결
- 수납

따라서 Windows에서 직접 Uvicorn을 실행한 개발 환경뿐 아니라 Multipass의 Docker 컨테이너에서도 동일한 애플리케이션이 정상 동작함을 확인하였다.


---

## 19. 최종 실행 구조

Article 3 완료 시점의 실행 구조는 다음과 같다.

```text
Windows 브라우저
        │
        │ http://172.24.214.37:8000
        ▼
Multipass VM
172.24.214.37
        │
        ├─ Docker
        │    │
        │    └─ academy-student-manager
        │         │
        │         └─ FastAPI + Uvicorn
        │
        └─ MySQL
             │
             └─ academy_student_db
```

FastAPI 애플리케이션과 MySQL은 동일한 Multipass VM에 있지만 FastAPI는 Docker 컨테이너 내부에서 실행되고 MySQL은 VM에서 실행되는 구조이다.


---

## 20. 기능명세서 기준 구현 확인

Article 3까지 구현한 기능을 최초 기능명세서와 비교하였다.

| 기능 ID | 기능 | 구현 상태 |
|---|---|---|
| DASHBOARD-001 | 운영 현황 조회 | 완료 |
| STUDENT-001 | 전체 학생 조회 | 완료 |
| STUDENT-002 | 학생 상세 조회 | 완료 |
| STUDENT-003 | 반별 학생 조회 | 완료 |
| ATTENDANCE-001 | 출결 조회 | 완료 |
| ATTENDANCE-002 | 출결 기록 | 완료 |
| PAYMENT-001 | 월별 수납 현황 조회 | 완료 |
| PAYMENT-002 | 납부 상태 처리 | 완료 |

계획했던 핵심 기능 8개가 모두 Web 화면에서 실제 동작하는 것을 확인하였다.


---

## 21. Article 3 최종 체크리스트

### Web

- [x] FastAPI에서 정적 파일 제공
- [x] 대시보드 구현
- [x] 전체 학생 조회
- [x] 반별 학생 조회
- [x] 학생 상세 조회
- [x] 날짜별 출결 조회
- [x] 반별 출결 조회
- [x] 출결 등록
- [x] 월별 수납 조회
- [x] 납부 상태 필터
- [x] 반별 수납 조회
- [x] 납부 처리
- [x] 변경 결과 대시보드 반영

### Docker

- [x] Docker 실행 상태 확인
- [x] Dockerfile 작성
- [x] `.dockerignore` 작성
- [x] 프로젝트 파일 Multipass 전송
- [x] Docker 이미지 빌드
- [x] Docker 컨테이너 실행
- [x] 컨테이너에서 FastAPI 실행 확인
- [x] 컨테이너에서 MySQL 연결 확인
- [x] Windows 브라우저에서 Docker Web 서비스 접속 확인


---

## 22. Article 3 결과

Article 3에서는 Article 2에서 구현한 백엔드 API를 실제 Web 화면과 연결하였다.

학생, 출결, 수납 기능을 단순 API 수준에서 끝내지 않고 브라우저에서 직접 조회하고 처리할 수 있도록 구성하였다.

또한 애플리케이션을 Docker 이미지로 생성하고 Multipass 환경에서 컨테이너로 실행하였다.

최종적으로 다음 흐름이 모두 정상 동작함을 확인하였다.

```text
사용자
↓
Web 화면
↓
JavaScript fetch
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

Docker 환경에서는 다음 구조로 실행된다.

```text
Windows 브라우저
↓
Multipass
↓
Docker Container
↓
FastAPI
↓
MySQL
```

이로써 Article 3의 Web 화면 구현 및 Docker 실행환경 구축을 완료하였다.

다음 Article에서는 MCP 연동과 K3s 확장을 진행한다.