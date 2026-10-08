# Article 2. 백엔드 핵심 기능 및 API 구현

## 1. 작업 목표

Article 1에서 구축한 MySQL 데이터와 SQLAlchemy 연결 구조를 이용하여 학생 관리 시스템의 핵심 백엔드 기능을 구현한다.

학생 조회, 출결 관리, 수납 관리, 대시보드 기능을 코드 계층별로 분리하고 FastAPI REST API로 제공한다.

또한 외부 입력값에 Type Hint와 Pydantic 검증을 적용하고, 출결 중복 등록 및 중복 납부 처리와 같은 업무 규칙을 비즈니스 로직에 반영한다.


## 2. 구현 파일

Article 2에서 다음 파일을 추가하였다.

```text
app/
├─ schemas.py
├─ repositories.py
├─ services.py
└─ main.py
```

각 파일의 역할은 다음과 같다.

| 파일 | 역할 |
|---|---|
| `schemas.py` | API 입력·출력 데이터 구조 및 Pydantic 검증 |
| `repositories.py` | MySQL 데이터 조회·저장·수정 |
| `services.py` | 학생 관리 업무 규칙 및 비즈니스 로직 |
| `main.py` | FastAPI Endpoint 제공 |


## 3. Pydantic Schema 및 입력 검증

### 3.1 출결 상태

출결 상태는 다음 세 값만 허용하였다.

```text
출석
지각
결석
```

`AttendanceCreate` 모델에 Pydantic 검증을 적용하여 다른 값이 입력되면 요청을 거부하도록 구성하였다.

정상 입력:

```text
status = 출석
```

검증 결과:

```text
정상 통과
```

잘못된 입력:

```text
status = 조퇴
```

검증 결과:

```text
ValidationError
Input should be '출석', '지각' or '결석'
```

기능명세서에서 정의한 출결 상태가 실제 코드 검증 조건으로 적용된 것을 확인하였다.


## 4. 데이터 접근 계층

`repositories.py`에서 MySQL 데이터를 직접 조회하거나 변경하는 기능을 분리하였다.

### 학생

- 전체 학생 조회
- 학년별 학생 조회
- 학생 상세 조회
- 반별 학생 조회

### 출결

- 날짜별 출결 조회
- 반별 출결 조회
- 학생별 출결 조회
- 동일 학생·동일 날짜 출결 조회
- 출결 데이터 저장

### 수납

- 월별 수납 조회
- 납부 상태별 조회
- 반별 수납 조회
- 특정 수납 데이터 조회
- 수납 데이터 변경 저장

데이터 접근 코드와 비즈니스 로직을 분리하여 API 코드에서 직접 SQL을 처리하지 않도록 구성하였다.


## 5. 데이터 접근 기능 검증

전체 학생 조회 결과:

```text
60 김민준 홍서윤
```

전체 학생 60명이 정상 조회되었다.

중2반 학생 조회 결과:

```text
20 김서준 2 2
```

확인 내용:

- 중2반 학생: 20명
- 첫 학생: 김서준
- 학년: 2
- class_id: 2

반별 조회가 정상적으로 동작하는 것을 확인하였다.


## 6. 비즈니스 로직

`services.py`에서 데이터 조회·저장 외에 학생 관리 시스템의 업무 규칙을 구현하였다.


### 6.1 학생 상세 조회

학생 상세 조회 시 다음 데이터를 함께 제공하도록 구성하였다.

- 학생 기본 정보
- 최근 출결 3건
- 현재 월 수납 상태

검증 결과:

```text
김민준 3 납부
```

학생 정보, 최근 출결, 수납 정보가 정상적으로 함께 조회되었다.


### 6.2 출결 중복 방지

출결 등록 시 다음 순서로 검증한다.

```text
출결 등록 요청
    ↓
학생 존재 여부 확인
    ↓
동일 학생 + 동일 날짜 출결 존재 여부 확인
    ↓
기존 데이터 없음 → 저장
기존 데이터 있음 → 등록 거부
```

이미 당일 출결이 있는 학생에게 같은 날짜의 출결을 다시 등록한 결과:

```text
ValueError:
해당 학생의 출결이 이미 등록되어 있습니다.
```

DB의 UNIQUE 제약조건뿐 아니라 서비스 계층에서도 중복 등록을 사전에 차단하도록 구현하였다.


### 6.3 수납 처리

미납 수납 정보를 조회한 결과:

```text
payment_id: 7
student_id: 7
status: 미납
paid_at: None
```

해당 수납 건을 납부 처리한 결과:

```text
7 7 납부 2026-10-08
```

처리 내용:

- `status`: 미납 → 납부
- `paid_at`: 2026-10-08 기록

같은 수납 건을 다시 납부 처리한 결과:

```text
ValueError:
이미 납부 처리된 항목입니다.
```

중복 납부 처리가 정상적으로 차단되는 것을 확인하였다.


## 7. 대시보드 집계

학생, 출결, 수납 데이터를 이용하여 대시보드 요약 정보를 계산하도록 구현하였다.

초기 검증 결과:

```text
total_students: 60

grade_1_students: 20
grade_2_students: 20
grade_3_students: 20

today_present: 48
today_late: 8
today_absent: 4

monthly_paid: 52
monthly_unpaid: 8
```

학생 수는 다음과 같이 정상 집계되었다.

```text
중1반 20명
중2반 20명
중3반 20명
총 60명
```

출결도 다음 조건을 만족하였다.

```text
48 + 8 + 4 = 60
```

이후 수납 기능 테스트에서 미납 학생을 실제 납부 처리하면서 납부·미납 집계 값도 데이터 변경에 따라 갱신되는 것을 확인하였다.


## 8. FastAPI 구현

FastAPI에서 다음 8개 Endpoint를 구현하였다.

| Method | Endpoint | 기능 |
|---|---|---|
| GET | `/api/dashboard` | 대시보드 조회 |
| GET | `/api/students` | 전체·조건별 학생 조회 |
| GET | `/api/students/{student_id}` | 학생 상세 조회 |
| GET | `/api/classes/{class_id}/students` | 반별 학생 조회 |
| GET | `/api/attendance` | 출결 조회 |
| POST | `/api/attendance` | 출결 등록 |
| GET | `/api/payments` | 수납 조회 |
| PATCH | `/api/payments/{payment_id}` | 납부 처리 |

FastAPI Swagger 문서는 다음 주소에서 확인하였다.

```text
http://127.0.0.1:8000/docs
```

8개의 Endpoint가 모두 Swagger에 정상 등록된 것을 확인하였다.


## 9. API 조회 기능 검증

다음 조회 API를 Swagger에서 직접 실행하였다.

### 대시보드

```text
GET /api/dashboard
```

결과:

```text
200 OK
```

### 전체 학생 조회

```text
GET /api/students
```

결과:

```text
200 OK
```

학생 60명이 정상 반환되었다.

### 학생 상세 조회

```text
GET /api/students/1
```

결과:

```text
200 OK
```

학생 기본정보, 최근 출결, 현재 월 수납정보가 정상 반환되었다.

### 반별 학생 조회

```text
GET /api/classes/2/students
```

결과:

```text
200 OK
```

중2반 학생 20명이 정상 반환되었다.


## 10. 출결 API 검증

### 출결 조회

요청:

```text
GET /api/attendance

date = 2026-10-08
class_id = 1
```

결과:

```text
200 OK
```

중1반 학생 20명의 출결이 정상 조회되었다.


### 출결 신규 등록

요청:

```json
{
  "student_id": 1,
  "attendance_date": "2026-10-01",
  "status": "출석",
  "note": "API 테스트"
}
```

결과:

```text
201 Created
```

생성된 출결:

```text
attendance_id: 421
student_id: 1
attendance_date: 2026-10-01
status: 출석
note: API 테스트
```


### 출결 중복 등록

동일한 출결 데이터를 다시 등록하였다.

결과:

```text
409 Conflict
```

응답:

```text
해당 학생의 출결이 이미 등록되어 있습니다.
```

FastAPI에서도 서비스 계층의 출결 중복 방지 로직이 정상 적용되는 것을 확인하였다.


## 11. 수납 API 검증

### 미납 학생 조회

요청:

```text
GET /api/payments

month = 2026-10
status = 미납
```

결과:

```text
200 OK
```

조회 당시 미납 데이터 7건이 정상 반환되었다.


### 납부 상태 변경

미납 데이터의 `payment_id`를 이용하여 다음 API를 실행하였다.

```text
PATCH /api/payments/{payment_id}
```

결과:

```text
200 OK
```

변경 결과:

```text
status: 납부
paid_at: 2026-10-08
```

MySQL의 수납 상태가 실제로 변경되었다.


### 중복 납부 처리

동일한 `payment_id`로 다시 PATCH 요청을 실행하였다.

결과:

```text
409 Conflict
```

응답:

```text
이미 납부 처리된 항목입니다.
```

중복 납부 방지 로직이 API에서도 정상 동작하였다.


## 12. 전체 코드 흐름

Article 2 완료 후 백엔드 요청 흐름은 다음과 같다.

```text
Web / API Client
       ↓
FastAPI Endpoint
       ↓
Pydantic 검증
       ↓
services.py
비즈니스 로직
       ↓
repositories.py
데이터 접근
       ↓
SQLAlchemy
       ↓
Multipass MySQL
```


## 13. 작업 중 확인 사항 및 이슈

### Pydantic 입력값 검증

기능명세에 없는 `조퇴` 값을 테스트하여 Pydantic이 입력 단계에서 잘못된 데이터를 차단하는 것을 확인하였다.

이는 오류가 아니라 검증 기능의 정상 동작을 확인하기 위한 테스트였다.


### 출결 중복 등록

동일 학생의 동일 날짜 출결을 다시 등록할 경우 `ValueError` 및 HTTP `409 Conflict`가 발생하였다.

기능명세에서 정의한 중복 출결 방지 규칙이 정상 적용된 결과이다.


### 수납 중복 처리

이미 납부된 데이터를 다시 납부 처리하면 `ValueError` 및 HTTP `409 Conflict`가 발생하였다.

이 역시 의도한 비즈니스 규칙의 정상 동작이다.


### 테스트에 따른 데이터 상태 변경

수납 처리 테스트 과정에서 실제 MySQL 데이터의 일부 미납 항목을 납부 상태로 변경하였다.

따라서 초기 데이터의 납부·미납 수와 현재 데이터베이스의 납부·미납 수는 테스트 이후 달라질 수 있다.

대시보드가 변경된 실제 DB 상태를 기준으로 다시 집계하는 것을 확인하였다.


## 14. Article 2 완료 상태

- [x] Pydantic Schema 작성
- [x] Type Hint 적용
- [x] 출결 상태 입력 검증
- [x] 학생 데이터 접근 함수
- [x] 출결 데이터 접근 함수
- [x] 수납 데이터 접근 함수
- [x] 학생 상세 비즈니스 로직
- [x] 출결 중복 방지
- [x] 수납 처리
- [x] 중복 납부 방지
- [x] 대시보드 집계
- [x] FastAPI Endpoint 8개 구현
- [x] Swagger API 문서 확인
- [x] 학생 조회 API 검증
- [x] 출결 조회·등록 API 검증
- [x] 출결 중복 API 검증
- [x] 수납 조회·처리 API 검증
- [x] 수납 중복 API 검증

**Article 2 완료**