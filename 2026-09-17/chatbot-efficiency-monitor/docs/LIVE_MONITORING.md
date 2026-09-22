# 실시간 저장과 주기별 모니터링

## 목적

직원이 챗봇을 사용할 때마다 원본 로그는 즉시 SQLite에 저장한다. 다만 관리자 화면에서 매 요청마다 분석을 다시 하지 않고, 일정 주기로 집계하여 대시보드와 이상치 알림에 반영한다.

```text
employee_chatbot.py
      │
      │ 사용 즉시
      ▼
live_chatbot_logs
      │
      │ MONITOR_INTERVAL_SECONDS
      ▼
scripts/hourly_monitor.py
      │
      ├─ hourly_snapshots
      ├─ hourly_employee_snapshots
      ├─ 이상치 탐지
      └─ alert_history → Webhook / Email(선택)
      │
      ▼
app.py 실시간 운영 탭
```

## 주기 변경

`monitoring/config.py`의 아래 값만 수정한다.

```python
# 개발 테스트: 1분
MONITOR_INTERVAL_SECONDS = 60

# 발표/실제 운영: 1시간
MONITOR_INTERVAL_SECONDS = 3600
```

## 저장되는 주요 데이터

- 직원 ID
- 문의 부서/카테고리
- 질문 유형(메뉴/텍스트)
- 라우팅 결과
- API 필요 여부
- 해결/담당자 전환 여부
- 응답 처리시간
- Input/Output Token
- API 호출/Retry
- HTTP 상태/오류 유형
- API 비용
- 이상치 후보 여부

질문 원문은 이메일과 긴 숫자를 최소 마스킹하고 200자로 제한한다. 실제 운영에서는 회사 개인정보/기밀정보 정책에 맞춰 더 강한 마스킹 또는 원문 미저장을 권장한다.

## 알림 순서

1. `ALERT_WEBHOOK_URL`이 있으면 Webhook 전송
2. Webhook이 없거나 실패하면 SMTP 이메일 전송
3. 둘 다 없으면 `alert_history`에만 기록

알림 전송 실패가 모니터링 프로세스 자체를 중단시키지 않도록 분리했다.

## 테스트

```bash
# 터미널 1
streamlit run employee_chatbot.py --server.port 8501

# 터미널 2
streamlit run app.py --server.port 8502

# 터미널 3
python scripts/hourly_monitor.py
```

실제 LLM API가 없는 상태에서 이상치 테스트:

```bash
python scripts/simulate_live_usage.py --anomaly
```

개발 설정에서는 최대 1분 후 대시보드의 `실시간 운영` 탭과 `alert_history`에서 결과를 확인한다.
