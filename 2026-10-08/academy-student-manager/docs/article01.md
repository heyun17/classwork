# Article 1. 개발 기반 및 데이터베이스 구축

## 1. 작업 목표

Windows에서 Python 애플리케이션을 개발하고 Multipass Ubuntu VM의 MySQL을 데이터베이스 서버로 사용하는 개발 환경을 구축한다.

또한 학생 관리 시스템에 필요한 데이터 모델과 초기 데이터를 생성하여 이후 API 개발에 사용할 데이터 기반을 준비한다.

## 2. 개발환경 구성

### Windows

- Python 3.13.15
- Python 가상환경 `.venv`
- FastAPI
- SQLAlchemy
- PyMySQL
- python-dotenv
- VS Code

### Multipass Ubuntu

- Ubuntu 24.04 LTS
- MySQL 8.0.46
- Docker
- K3s

## 3. 프로젝트 기본 구조

```text
academy-student-manager/
├─ .venv/
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ database.py
│  ├─ models.py
│  └─ seed.py
├─ docs/
├─ .env
├─ .gitignore
└─ requirements.txt
```

## 4. MySQL 구성

프로젝트 전용 데이터베이스와 사용자를 생성하였다.

- Database: `academy_student_db`
- User: `academy_user`
- Port: `3306`
- Character Set: `utf8mb4`

DB 접속 정보는 Python 코드에 직접 작성하지 않고 `.env`에서 관리하도록 구성하였다.

## 5. Windows와 MySQL 연결

초기 MySQL 설정에서는 다음과 같이 로컬 인터페이스에서만 접속을 받고 있었다.

```text
bind-address = 127.0.0.1
```

Windows 애플리케이션에서 Multipass VM의 MySQL에 접속할 수 있도록 다음과 같이 변경하였다.

```text
bind-address = 0.0.0.0
```

이후 Windows의 PyMySQL과 SQLAlchemy를 이용하여 MySQL 연결을 각각 검증하였다.

검증 결과:

```text
MySQL connection OK
SQLAlchemy connection OK
```

## 6. 데이터 모델

다음 4개 테이블을 구성하였다.

### classes

- 반 ID
- 반 이름
- 학년
- 정원

### students

- 학생 ID
- 이름
- 학년
- 학교
- 보호자 연락처
- 재원 상태
- 소속 반

### attendance

- 출결 ID
- 학생 ID
- 날짜
- 출결 상태
- 비고

동일 학생의 동일 날짜 출결이 중복되지 않도록 제약조건을 설정하였다.

### payments

- 수납 ID
- 학생 ID
- 대상 월
- 수강료
- 납부 상태
- 납부일

동일 학생의 동일 월 수납 정보가 중복되지 않도록 제약조건을 설정하였다.

## 7. 초기 데이터 구성

### 반

- 중1반: 20명
- 중2반: 20명
- 중3반: 20명

총 3개 반을 구성하였다.

### 학생

총 60명의 학생 데이터를 생성하였다.

### 출결

최근 7일 동안 학생 60명의 출결 데이터를 생성하였다.

```text
60명 × 7일 = 420건
```

출결 상태:

- 출석
- 지각
- 결석

### 수납

학생 60명의 현재 월 수납 정보를 생성하였다.

상태:

- 납부
- 미납

## 8. 최종 검증 결과

```text
classes: 3
students: 60
attendance: 420
payments: 60
```

MySQL에서 직접 조회하여 학생 데이터와 당일 출결 데이터가 정상적으로 저장된 것을 확인하였다.

## 9. 작업 중 이슈 및 처리

### MySQL 외부 접속 제한

MySQL이 `127.0.0.1:3306`에만 바인딩되어 있어 Windows에서 직접 접속할 수 없는 상태였다.

`mysqld.cnf`의 `bind-address`를 `0.0.0.0`으로 변경하고 MySQL을 재시작하여 해결하였다.

### VS Code SSH 접속

기존 SSH 연결 자체는 정상적으로 작동했지만 VS Code Remote SSH 사용 과정에서 기존 창이 재사용되어 Windows 작업창과 Ubuntu 작업창이 분리되지 않는 상황이 발생하였다.

작업창을 다시 분리하고 Ubuntu 서버 작업은 Multipass 환경을 이용하여 계속 진행하였다.

## 10. Article 1 완료 상태

- [x] Windows Python 개발환경 구성
- [x] `.env` 기반 DB 환경설정
- [x] Multipass MySQL 확인
- [x] Windows → Multipass MySQL 연결
- [x] SQLAlchemy DB 연결 모듈
- [x] 데이터 모델 작성
- [x] MySQL 테이블 생성
- [x] 학생 60명 초기 데이터 생성
- [x] 출결 데이터 생성
- [x] 수납 데이터 생성
- [x] MySQL 실제 데이터 검증

**Article 1 완료**