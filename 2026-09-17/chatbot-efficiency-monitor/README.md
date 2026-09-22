# 사내 챗봇 비용 · 자원 절감 모니터링

시스템 엔지니어 관점에서 사내 챗봇 도입 전후의 **문의량, 사람 처리시간, 해결률, 상담원 전환율, 토큰/API 비용, 시스템 상태**를 비교하는 실습 프로젝트입니다.

> 데이터와 회사는 모두 가상입니다. `GaonWorks Services`라는 620명 규모의 IT 서비스 회사를 가정했습니다.

## 왜 이 회사가 적합한가

- 직원 수가 충분해 전산/인사/법률/회계 등 지원부서 문의가 반복적으로 발생한다.
- 비밀번호, VPN, 연차, 증명서, 회의실, 정산처럼 정형화 가능한 질문이 많다.
- 단순 FAQ는 AI 없이 처리하고 복잡한 업무 질문만 LLM에 보내 비용을 줄이기 쉽다.
- 보안/권한 요청은 자동 처리하지 않고 담당자에게 넘기는 통제가 필요하다.

## 핵심 가설

챗봇 도입 전에는 전산·인사·법률·회계 등 지원부서 직원들이 직접 받는 문의가 월평균 약 500건이었다. 이 과정에서 지원부서 직원들은 반복적인 문의에 답변하는 데 업무 시간을 사용해야 했고, 그만큼 본래 담당 업무에 집중할 수 있는 시간이 줄어들었다.

챗봇 도입 후에는 월평균 챗봇 세션이 약 3,000건으로 증가했다. 하지만 챗봇 사용량이 늘었다는 사실만으로 업무 효율이 높아졌다고 판단하기는 어렵다. 실제로 인적 자원이 얼마나 절감되었는지, 챗봇이 문의를 얼마나 잘 해결하고 있는지, 그리고 토큰·API 비용 대비 효과가 있는지를 함께 확인해야 한다. 따라서 다음 지표를 함께 본다.

- 업무 질문 해결률
- 상담원 전환율
- 평균 해결시간
- API를 쓰지 않은 비율
- 토큰/API 비용
- 대체된 인적 처리시간과 금액
- 비업무/비효율 세션

## 빠른 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_test_data.py
python scripts/build_db.py
```

직원용 챗봇 UI:

```bash
streamlit run employee_chatbot.py
```

시스템 엔지니어용 모니터링 대시보드:

```bash
streamlit run app.py
```

직원용 챗봇, 관리자 대시보드, 주기 집계 프로세스를 같이 테스트하려면 터미널을 3개 엽니다.

```bash
# 터미널 1 - 직원용 챗봇
streamlit run employee_chatbot.py --server.port 8501

# 터미널 2 - 관리자 대시보드
streamlit run app.py --server.port 8502

# 터미널 3 - 주기별 집계 + 이상치 탐지 + 알림
python scripts/hourly_monitor.py
```

직원 챗봇 사용 기록은 질문/메뉴 사용 시점에 즉시 SQLite의 `live_chatbot_logs`에 저장됩니다. 관리자 대시보드는 원본 로그를 매번 직접 읽지 않고, 모니터 프로세스가 만든 주기 집계 결과를 보여줍니다.

테스트:

```bash
python -m pytest -q
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/build_db.py
streamlit run employee_chatbot.py
# 별도 PowerShell 창에서: streamlit run app.py --server.port 8502
python -m pytest -q
```

## 가상환경과 Git 협업

가상환경 폴더 `.venv/` 자체는 Git에 올리지 않습니다. 각 팀원은 `requirements.txt`로 동일한 패키지를 설치합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

설치 후 Git에는 코드와 `requirements.txt`만 올립니다.

```bash
git add .
git commit -m "chore: add project requirements"
git push
```

`.gitignore`에 `.venv/`, `.env`, `__pycache__/`가 포함되어 있어 가상환경과 비밀키는 커밋되지 않습니다.


## 화면 분리

- `employee_chatbot.py`: 직원이 사용하는 챗봇 화면입니다. ChatGPT처럼 대화가 쌓이고, 자주 묻는 질문은 버튼으로 바로 선택할 수 있습니다. FAQ와 보안/권한 요청은 LLM API 없이 처리합니다. `심심해`, `놀자`, `뭐해`처럼 명백한 잡담성 질문만 API 호출 전에 차단하며, 월급·구내식당·인터넷 장애처럼 업무 가능성이 있는 질문은 함부로 차단하지 않고 FAQ 또는 AI 처리 단계로 넘깁니다.
- `app.py`: 시스템 엔지니어가 보는 관리자 화면입니다. 문의량, 해결률, 상담원 전환율, 토큰/API 비용, 이상치, 시스템 상태를 모니터링합니다.

직원 화면에는 운영용 상세 지표를 노출하지 않고, 관리자 대시보드에는 챗봇 대화 UI를 넣지 않아 역할을 분리했습니다.

## 실시간 저장 · 주기 집계 · 이상치 알림

운영 흐름은 다음과 같습니다.

```text
직원 챗봇 사용
   ↓ 즉시 저장
live_chatbot_logs
   ↓ 주기 집계
hourly_snapshots / hourly_employee_snapshots
   ↓
이상치 탐지 → alert_history → Webhook/이메일(선택)
   ↓
관리자 대시보드
```

### 개발 중에는 1분, 발표/운영에서는 1시간

주기는 **한 파일의 한 줄만 수정**하면 됩니다.

`monitoring/config.py`

```python
# 현재 개발 테스트: 1분
MONITOR_INTERVAL_SECONDS = 60

# ★ 발표/운영에서 1시간으로 바꿀 때
MONITOR_INTERVAL_SECONDS = 3600
```

이 값을 모니터 프로세스와 관리자 대시보드 자동 새로고침이 같이 사용합니다.

### 1분 테스트 방법

1. 터미널 3개에서 직원 챗봇, 관리자 대시보드, `hourly_monitor.py`를 실행합니다.
2. 직원용 챗봇에서 질문을 몇 번 입력합니다.
3. 질문 직후 DB에는 즉시 저장됩니다.
4. 최대 1분 뒤 관리자 대시보드의 **실시간 운영** 탭에 집계 결과가 나타납니다.

실제 API가 아직 연결되지 않아 Token/오류 이상치까지 시험하기 어렵다면 개발 전용 시뮬레이터를 사용할 수 있습니다.

```bash
python scripts/simulate_live_usage.py --anomaly
```

이 명령은 테스트용 토큰 과다, 재시도, Timeout 데이터를 DB에 넣습니다. 최대 1분 뒤 이상치 알림이 생성되는지 확인합니다. 발표용 실데이터로 사용하지 않습니다.

### 알림 설정

알림은 **대시보드/DB 기록이 기본**이고, 선택적으로 Webhook 또는 이메일을 사용할 수 있습니다. 운영팀이 함께 확인할 수 있어 Webhook(Slack 등)을 우선하도록 구성했습니다.

```bash
cp .env.example .env
```

`.env`에서 `ALERT_WEBHOOK_URL`을 설정하면 Webhook을 우선 사용합니다. Webhook이 없거나 전송에 실패하면 SMTP 이메일 설정을 확인합니다. 둘 다 설정하지 않아도 `alert_history`에는 이상치가 기록됩니다. `.env`는 Git에 올리지 않습니다.

### 현재 이상치 후보

- API 최종 오류 / 오류율 증가
- API Retry 증가
- 세션당 Token 과다
- 부서 평균 대비 직원 Token 급증
- 업무질문 해결률 저하
- 동일 직원의 명백한 잡담 반복

직원별 Token이 많다는 이유만으로 문제 사용자로 판단하지 않고, **세션 수·세션당 Token·Retry·오류·해결률을 함께 확인**하도록 설계했습니다.

## DB 확인

```bash
sqlite3 database/chatbot_monitor.db
```

```sql
.tables
SELECT route, COUNT(*) FROM chatbot_logs GROUP BY route;
SELECT department, AVG(resolved) * 100 AS resolution_rate
FROM chatbot_logs
WHERE route <> 'NON_WORK'
GROUP BY department;
```

## 프로젝트 구조

```text
chatbot-roi-dashboard/
├── employee_chatbot.py      # 직원용 챗봇 UI
├── app.py                   # 시스템 엔지니어용 모니터링 대시보드
├── README.md
├── TASK.md
├── requirements.txt
├── analysis/
├── chatbot/
├── monitoring/             # 실시간 저장·집계·이상치·알림
├── data/
├── database/
├── docs/
├── scripts/                # hourly_monitor.py 포함
├── tests/
└── .github/workflows/ci.yml
```

## 비용 절감 설계

1. 자주 쓰는 질문은 클릭 메뉴로 제공한다.
2. FAQ 키워드가 일치하면 LLM을 호출하지 않는다.
3. 권한/보안 요청은 담당자 절차로 전환하고 LLM을 호출하지 않는다.
4. `심심해`, `놀자`, `뭐해`처럼 명백한 잡담성 질문만 API 호출 전에 차단하고 이상치 후보로 기록한다. 그 외 애매한 질문은 업무 가능성을 열어두고 AI 처리 단계로 넘긴다.
5. 위 규칙으로 해결되지 않은 업무 질문만 LLM 대상으로 보낸다.
6. 실운영에서는 프롬프트 길이 제한, 응답 길이 상한, 대화 요약, 캐시, 작은 모델 우선 라우팅을 추가한다.

## 주의

`company_profile.csv`의 토큰 단가/인건비/고정비는 실습용 가정값입니다. 실제 운영 평가에서는 사용하는 모델, 클라우드, 로그 보관, DB, 보안 솔루션의 실제 계약 단가로 교체해야 합니다.
