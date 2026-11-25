# ====================================================================
# A4-M7 설정 — 답변 생성(LLM), 가격, 운영 기준선과 Alert 규칙
# A4-M6의 config.py(경로·청킹·K)는 그대로 쓰고, 여기에는 M7에서 새로 생긴 값만 둔다.
# ====================================================================
import os
from config import BASE_DIR, DATA_DIR, OUT_DIR  # noqa: F401  (경로·.env 로드 공유)

# --- 검색 (A4-M6에서 고른 조합: Metadata+BM25 · heading) ---------------
RETRIEVER = "Metadata+BM25"
CHUNK_METHOD = "heading"
ANSWER_K = int(os.getenv("ANSWER_K", "5"))   # LLM에 넘길 청크 수 (미션 3에서 바꿔 봄)

# --- 답변 생성 ---------------------------------------------------------
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-6-luna")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-6-luna")
# openai: 실제 호출 / fake: 키 없이 흐름만 (답변·시간·토큰은 '흉내낸 값')
LLM_BACKEND = os.getenv("LLM_BACKEND", "openai")
MAX_RETRIES = 3
NO_ANSWER_TEXT = "제공된 문서에서 확인할 수 없습니다."

# --- 가격 (USD / 1M 토큰) — 강의 시점에 OpenAI 가격 페이지에서 확인 후 수정 --------
PRICE = {
    "gpt-6-luna": {"input": 0.10, "output": 0.50},
}
USD_KRW = 1400   # 원화 환산용 (대략값)

# --- 운영 Alert 규칙 -----------------------------------------------------
# 절대 기준 (서비스 요구사항) — 업계 표준값이 아니라 이 실습용 예시
ALERT_ABS = {
    "retrieval_hit":        (">=", 0.90),   # 정답 문서가 근거에 들어간 비율
    "grounded_rule":        (">=", 0.90),   # 규칙 기반 근거성
    "citation_valid":       (">=", 0.95),   # 존재하는 근거만 인용했나
    "abstention_accuracy":  (">=", 0.80),   # 답할 수 없는 질문에서 보류한 비율
    "e2e_p95_ms":           ("<=", 5000),
    "error_rate":           ("<=", 0.02),
}
# 기준선 대비 상대 변화 — 기준선보다 이만큼 나빠지면 Alert
ALERT_REL = {
    "avg_input_tokens":     ("up", 0.30),   # 30% 이상 증가
    "cost_per_q_usd":       ("up", 0.30),
    "e2e_p95_ms":           ("up", 0.50),
    "grounded_rule":        ("down", 0.05),
    "retrieval_hit":        ("down", 0.05),
}
