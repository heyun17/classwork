from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import calendar
import random

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEED = 20260917
rng = random.Random(SEED)

# -----------------------------------------------------------------------------
# 1) 챗봇 도입 전 테스트 데이터
#    2026-01 ~ 2026-06, 매월 정확히 500건
# -----------------------------------------------------------------------------
BASELINE_CATEGORIES = {
    "전산": ["PC 장애", "인터넷 연결", "메일 오류", "VPN 연결", "비밀번호 초기화", "프로그램 설치", "계정 잠금"],
    "인사": ["급여 문의", "연차 잔여일", "재직증명서", "근태", "복지", "출산휴가", "퇴직금"],
    "총무": ["회의실 예약", "주차", "비품", "사내 행사", "구내식당 메뉴"],
    "재무": ["법인카드 정산", "경비처리", "세금계산서", "출장비"],
    "법무": ["계약서 검토", "사내 규정", "개인정보 문의", "법률 문의"],
    "보안": ["권한 요청", "보안 신고", "접근 통제", "MFA 오류"],
}
DEPARTMENT_WEIGHTS = {
    "전산": 0.35,
    "인사": 0.22,
    "총무": 0.13,
    "재무": 0.12,
    "법무": 0.08,
    "보안": 0.10,
}
HANDLE_TIME = {
    "전산": (8, 18),
    "인사": (7, 15),
    "총무": (5, 12),
    "재무": (8, 17),
    "법무": (12, 24),
    "보안": (10, 22),
}


def weighted_choice(weight_map: dict[str, float]) -> str:
    names = list(weight_map)
    weights = [weight_map[n] for n in names]
    return rng.choices(names, weights=weights, k=1)[0]


def random_datetime_in_month(year: int, month: int) -> datetime:
    last_day = calendar.monthrange(year, month)[1]
    day = rng.randint(1, last_day)
    hour = rng.randint(8, 19)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    return datetime(year, month, day, hour, minute, second)


baseline_rows: list[dict] = []
inquiry_no = 1
for month in range(1, 7):
    for _ in range(500):
        department = weighted_choice(DEPARTMENT_WEIGHTS)
        category = rng.choice(BASELINE_CATEGORIES[department])
        low, high = HANDLE_TIME[department]
        handle_minutes = round(rng.uniform(low, high), 1)
        baseline_rows.append(
            {
                "inquiry_id": f"I{inquiry_no:06d}",
                "created_at": random_datetime_in_month(2026, month).strftime("%Y-%m-%d %H:%M:%S"),
                "department": department,
                "category": category,
                "human_handle_minutes": handle_minutes,
                "resolved": 1 if rng.random() < 0.96 else 0,
            }
        )
        inquiry_no += 1

baseline_df = pd.DataFrame(baseline_rows).sort_values("created_at")
baseline_df.to_csv(DATA_DIR / "pre_chatbot_inquiries.csv", index=False, encoding="utf-8-sig")

# -----------------------------------------------------------------------------
# 2) 챗봇 도입 후 테스트 데이터
#    2026-07 ~ 2026-09, 매월 정확히 3,000세션
#
# 핵심 정책
# - FAQ/메뉴: API 0
# - 보안/권한: API 0, 담당자 절차 안내
# - NON_WORK: '심심해/놀자/뭐해' 같은 명백한 잡담만 차단
# - 그 외 FAQ로 해결되지 않는 질문: LLM API 사용
# -----------------------------------------------------------------------------
FAQ_ITEMS = [
    ("전산", "비밀번호 초기화", "비밀번호를 잊어버렸어요"),
    ("전산", "VPN 연결", "VPN 연결 방법 알려줘"),
    ("인사", "연차 잔여일", "연차가 몇 일 남았는지 확인하고 싶어"),
    ("인사", "재직증명서", "재직증명서는 어디서 발급해?"),
    ("인사", "급여 문의", "월급 지급일과 급여명세서 확인 방법 알려줘"),
    ("총무", "회의실 예약", "회의실 예약 방법 알려줘"),
    ("재무", "법인카드 정산", "법인카드 정산 방법 알려줘"),
]

SECURITY_ITEMS = [
    ("보안", "권한 요청", "관리자 권한을 부여해줘"),
    ("보안", "접근 권한", "접근 권한을 바로 열어줘"),
    ("전산", "프로그램 설치", "관리자 권한이 필요한 프로그램을 설치해줘"),
    ("보안", "방화벽", "방화벽을 해제해줘"),
]

# FAQ에 정확히 등록되지 않은 사내 질문. 보수적으로 차단하지 않고 API로 전달한다.
LLM_ITEMS = [
    ("전산", "인터넷 연결", "인터넷 연결이 안돼. 어디부터 확인해야 해?"),
    ("전산", "메일 오류", "사내 메일 첨부파일 전송이 계속 실패해"),
    ("전산", "PC 장애", "컴퓨터가 갑자기 느려지고 멈춰"),
    ("전산", "계정 잠금", "로그인을 여러 번 실패해서 계정이 잠긴 것 같아"),
    ("전산", "프린터", "사무실 프린터가 오프라인으로 보여"),
    ("인사", "출산휴가", "출산휴가 신청 절차와 필요한 서류를 알려줘"),
    ("인사", "복지", "올해 건강검진 복지 지원 범위를 알려줘"),
    ("인사", "근태", "외근한 날 근태 입력을 어떻게 수정해?"),
    ("인사", "퇴직금", "퇴직금 관련 사내 신청 절차는 어떻게 돼?"),
    ("총무", "구내식당 메뉴", "오늘 구내식당 메뉴가 뭐야?"),
    ("총무", "주차", "방문 차량 주차 등록 절차를 알려줘"),
    ("총무", "비품", "모니터 추가 지급을 신청하려면 어떻게 해야 해?"),
    ("총무", "사내 행사", "이번 달 사내 행사 일정이 있는지 알려줘"),
    ("재무", "경비처리", "해외 출장 택시비는 어떤 항목으로 처리해?"),
    ("재무", "세금계산서", "세금계산서가 반려됐는데 수정 절차를 알려줘"),
    ("재무", "출장비", "출장비 정산 기준을 확인하고 싶어"),
    ("법무", "계약서 검토", "협력사 계약서 검토 요청 절차를 알려줘"),
    ("법무", "개인정보 문의", "고객 개인정보 보관기간에 대한 사내 기준을 알려줘"),
    ("법무", "사내 규정", "외부 자료를 발표에 인용할 때 사내 절차가 있어?"),
    ("보안", "MFA 오류", "MFA 인증번호가 계속 실패해"),
]

# 확실한 잡담만 NON_WORK로 분류한다.
NON_WORK_QUESTIONS = [
    "심심해",
    "나랑 놀자",
    "지금 뭐해?",
    "재밌는 얘기 해줘",
    "끝말잇기 하자",
    "농담 하나 해줘",
    "나랑 대화하자",
]

# 정확히 9,000건을 만들기 위한 전체 라우팅 비중.
ROUTE_COUNTS = {
    "MENU_FAQ": 2100,
    "TEXT_FAQ": 1800,
    "SECURITY_ESCALATE": 350,
    "NON_WORK": 90,
    "LLM": 4660,
}
assert sum(ROUTE_COUNTS.values()) == 9000

routes: list[str] = []
for route, count in ROUTE_COUNTS.items():
    routes.extend([route] * count)
rng.shuffle(routes)

# 각 달 3,000건 보장
month_slots = [7] * 3000 + [8] * 3000 + [9] * 3000
rng.shuffle(month_slots)

INPUT_COST_PER_1M = 3000
OUTPUT_COST_PER_1M = 12000


def build_api_usage(department: str, category: str) -> tuple[int, int, int, int, str, int, float, int]:
    """LLM 호출의 token/error/retry 정보를 생성한다.

    반환: input_tokens, output_tokens, status_code, retry_count,
          error_type, api_call_count, api_cost_krw, anomaly_flag
    """
    complexity = 1.0
    if department == "법무":
        complexity = 1.8
    elif category in {"세금계산서", "출장비", "개인정보 문의"}:
        complexity = 1.35

    input_tokens = int(rng.uniform(650, 1800) * complexity)
    output_tokens = int(rng.uniform(180, 650) * complexity)

    # 긴 컨텍스트/RAG 과다 같은 비용 이상치를 소량 포함한다.
    anomaly_flag = 0
    if rng.random() < 0.018:
        input_tokens += rng.randint(6500, 14000)
        output_tokens += rng.randint(600, 1800)
        anomaly_flag = 1

    error_type = ""
    retry_count = 0
    status_code = 200

    # 약 3%에서 일시적 API 오류/재시도를 발생시킨다.
    if rng.random() < 0.03:
        error_type, first_code = rng.choice(
            [("rate_limit", 429), ("timeout", 504), ("server_error", 500)]
        )
        retry_count = rng.choices([1, 2, 3], weights=[0.72, 0.23, 0.05], k=1)[0]
        # 대부분 재시도로 회복하지만 일부는 최종 실패한다.
        recovered = rng.random() < 0.82
        status_code = 200 if recovered else first_code
        # 재시도에도 입력 토큰이 다시 사용되는 상황을 단순화해 반영한다.
        input_tokens = int(input_tokens * (1 + 0.75 * retry_count))
        output_tokens = int(output_tokens * (1 + 0.20 * retry_count))
        if retry_count >= 2 or not recovered:
            anomaly_flag = 1

    api_call_count = 1 + retry_count
    api_cost_krw = (
        input_tokens / 1_000_000 * INPUT_COST_PER_1M
        + output_tokens / 1_000_000 * OUTPUT_COST_PER_1M
    )
    return (
        input_tokens,
        output_tokens,
        status_code,
        retry_count,
        error_type,
        api_call_count,
        round(api_cost_krw, 3),
        anomaly_flag,
    )


chat_rows: list[dict] = []
for idx, (route, month) in enumerate(zip(routes, month_slots), start=1):
    employee_id = f"E{rng.randint(1, 620):04d}"
    created_at = random_datetime_in_month(2026, month)

    input_tokens = 0
    output_tokens = 0
    api_cost_krw = 0.0
    status_code = 0
    retry_count = 0
    error_type = ""
    api_call_count = 0
    anomaly_flag = 0
    human_handle_minutes = 0.0

    if route in {"MENU_FAQ", "TEXT_FAQ"}:
        department, category, question_text = rng.choice(FAQ_ITEMS)
        question_type = "menu" if route == "MENU_FAQ" else "text"
        resolved = 1 if rng.random() < 0.965 else 0
        escalated = 0 if resolved else 1
        resolution_seconds = round(rng.uniform(5, 40), 1)
        message_count = rng.choice([1, 1, 1, 2])
        if escalated:
            human_handle_minutes = round(rng.uniform(4, 12), 2)

    elif route == "SECURITY_ESCALATE":
        department, category, question_text = rng.choice(SECURITY_ITEMS)
        question_type = "text"
        resolved = 0
        escalated = 1
        resolution_seconds = round(rng.uniform(8, 45), 1)
        message_count = rng.choice([1, 2])
        human_handle_minutes = round(rng.uniform(6, 18), 2)

    elif route == "NON_WORK":
        department = rng.choice(["전산", "인사", "총무", "재무", "법무", "보안"])
        category = "잡담"
        question_text = rng.choice(NON_WORK_QUESTIONS)
        question_type = "text"
        resolved = 0
        escalated = 0
        resolution_seconds = round(rng.uniform(2, 8), 1)
        message_count = 1
        anomaly_flag = 1

    else:  # LLM
        department, category, question_text = rng.choice(LLM_ITEMS)
        question_type = "text"
        (
            input_tokens,
            output_tokens,
            status_code,
            retry_count,
            error_type,
            api_call_count,
            api_cost_krw,
            token_anomaly,
        ) = build_api_usage(department, category)
        anomaly_flag = max(anomaly_flag, token_anomaly)

        success = status_code == 200
        base_resolve_prob = 0.80 if success else 0.05
        if department == "법무":
            # 법무는 답변 참고 후 담당자 확인으로 넘어가는 비율을 높인다.
            base_resolve_prob -= 0.12
        resolved = 1 if rng.random() < base_resolve_prob else 0
        escalated = 0 if resolved else 1
        resolution_seconds = round(
            rng.uniform(35, 180) + retry_count * rng.uniform(25, 80), 1
        )
        message_count = rng.randint(2, 6) + min(retry_count, 2)
        if escalated:
            human_handle_minutes = round(rng.uniform(5, 20), 2)
        if status_code != 200:
            anomaly_flag = 1

    chat_rows.append(
        {
            "session_id": f"S{idx:06d}",
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "employee_id": employee_id,
            "department": department,
            "category": category,
            "question_text": question_text,
            "question_type": question_type,
            "route": route,
            "resolved": resolved,
            "escalated": escalated,
            "resolution_seconds": resolution_seconds,
            "message_count": message_count,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "api_call_count": api_call_count,
            "retry_count": retry_count,
            "status_code": status_code,
            "error_type": error_type,
            "api_cost_krw": api_cost_krw,
            "human_handle_minutes": human_handle_minutes,
            "anomaly_flag": anomaly_flag,
        }
    )

chat_df = pd.DataFrame(chat_rows).sort_values("created_at")
chat_df.to_csv(DATA_DIR / "chatbot_logs.csv", index=False, encoding="utf-8-sig")

print("테스트 데이터 생성 완료")
print(f"- pre_chatbot_inquiries: {len(baseline_df):,} rows")
print(f"- chatbot_logs: {len(chat_df):,} rows")
print("\n월별 챗봇 세션")
print(chat_df.assign(month=pd.to_datetime(chat_df["created_at"]).dt.to_period("M")).groupby("month").size())
print("\nRoute 분포")
print(chat_df["route"].value_counts())
print(f"\nNON_WORK 비율: {(chat_df['route'].eq('NON_WORK').mean()*100):.2f}%")
print(f"API 사용 비율: {(chat_df['api_call_count'].gt(0).mean()*100):.2f}%")
