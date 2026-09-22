from pathlib import Path
import time

import pandas as pd
import streamlit as st

from chatbot.router import menu_answer, route_question
from monitoring.live_store import log_chat_usage

ROOT = Path(__file__).resolve().parent
FAQ_PATH = ROOT / "data" / "faq.csv"

st.set_page_config(
    page_title="사내 업무 도우미",
    page_icon="💬",
    layout="centered",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 900px;
        padding-top: 1.4rem;
        padding-bottom: 5rem;
    }
    [data-testid="stSidebar"] {
        background: #f7f8fa;
    }
    .chat-header {
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 18px 20px;
        margin-bottom: 18px;
        background: white;
        box-shadow: 0 4px 18px rgba(0,0,0,0.04);
    }
    .chat-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .chat-subtitle {
        color: #6b7280;
        font-size: 0.92rem;
    }
    .quick-title {
        font-size: 0.92rem;
        font-weight: 700;
        margin: 6px 0 8px 0;
    }
    div[data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 0.25rem 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_faq() -> pd.DataFrame:
    return pd.read_csv(FAQ_PATH)


def route_label(result: dict) -> str:
    labels = {
        "MENU_FAQ": "빠른 메뉴 답변 · AI API 미사용",
        "TEXT_FAQ": "FAQ 자동 답변 · AI API 미사용",
        "SECURITY_ESCALATE": "보안/권한 요청 · 담당자 문의 필요",
        "NON_WORK": "명백한 잡담성 질문 · AI API 미사용",
        "LLM_REQUIRED": "복잡한 업무 질문 · 실제 운영 시 AI API 대상",
        "EMPTY": "입력 필요",
        "UNKNOWN_MENU": "등록되지 않은 메뉴",
    }
    return labels.get(result.get("route", ""), result.get("route", ""))


def add_exchange(user_text: str, result: dict) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "meta": route_label(result),
            "route": result["route"],
            "use_api": result["use_api"],
        }
    )


def save_usage(employee_id: str, user_text: str, result: dict, question_type: str, elapsed: float) -> None:
    """직원이 챗봇을 사용할 때마다 1건을 즉시 DB에 기록한다.

    현재 데모는 실제 LLM API를 호출하지 않는다. 따라서 LLM_REQUIRED도
    'API 필요' 여부만 저장하고 실제 token/api_call_count는 0으로 기록한다.
    추후 실제 API를 연결하면 응답 usage 값을 이 함수에 넘기면 된다.
    """
    route = result.get("route", "")
    resolved = int(route in {"MENU_FAQ", "TEXT_FAQ"})
    escalated = int(route == "SECURITY_ESCALATE")
    anomaly = int(result.get("anomaly", False))

    log_chat_usage(
        employee_id=employee_id,
        department=result.get("department", "미분류"),
        category=result.get("category", "미분류"),
        question_text=user_text,
        question_type=question_type,
        route=route,
        api_required=int(bool(result.get("use_api", False))),
        resolved=resolved,
        escalated=escalated,
        resolution_seconds=elapsed,
        message_count=1,
        input_tokens=0,
        output_tokens=0,
        api_call_count=0,
        retry_count=0,
        status_code=0,
        error_type=None,
        api_cost_krw=0.0,
        anomaly_flag=anomaly,
    )


faq = load_faq()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕하세요. 사내 업무 도우미입니다. 자주 찾는 메뉴를 누르거나 업무 관련 질문을 입력해주세요.",
            "meta": "FAQ 우선 처리로 불필요한 AI API 사용을 줄입니다.",
            "route": "WELCOME",
            "use_api": False,
        }
    ]

if "last_log_status" not in st.session_state:
    st.session_state.last_log_status = ""

with st.sidebar:
    st.header("직원용 챗봇")
    st.caption("실습용 화면")
    employee_id = st.text_input("직원 ID (데모)", value="E0001", help="실제 회사에서는 SSO 로그인 정보에서 자동으로 가져오는 값입니다.")
    st.markdown("**지원 범위**")
    st.write("전산 · 인사 · 총무 · 재무 · 법무 · 보안")
    st.markdown("**운영 원칙**")
    st.write("• 모든 사용 기록은 즉시 DB에 저장")
    st.write("• 자주 묻는 질문은 즉시 답변")
    st.write("• 보안/권한 요청은 담당자 안내")
    st.write("• 심심해·놀자·뭐해 같은 명백한 잡담만 AI 호출 전 차단")
    if st.session_state.last_log_status:
        st.caption(st.session_state.last_log_status)
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = st.session_state.messages[:1]
        st.rerun()

st.markdown(
    """
    <div class="chat-header">
        <div class="chat-title">💬 사내 업무 도우미</div>
        <div class="chat-subtitle">반복 문의는 빠르게 해결하고, 필요한 경우 담당 부서로 안내합니다.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="quick-title">자주 찾는 메뉴</div>', unsafe_allow_html=True)
menu_rows = faq.head(8).reset_index(drop=True)
cols = st.columns(4)
for i, row in menu_rows.iterrows():
    label = f"{row['department']} · {row['category']}"
    if cols[i % 4].button(label, key=f"quick_{row['menu_id']}", use_container_width=True):
        started = time.perf_counter()
        result = menu_answer(row["menu_id"], faq)
        elapsed = time.perf_counter() - started
        try:
            save_usage(employee_id, label, result, "menu", elapsed)
            st.session_state.last_log_status = "✓ 최근 사용 기록이 DB에 즉시 저장되었습니다."
        except Exception as exc:
            st.session_state.last_log_status = f"⚠ 로그 저장 실패: {type(exc).__name__}"
        add_exchange(label, result)
        st.rerun()

st.divider()

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("meta"):
            st.caption(msg["meta"])

question = st.chat_input("업무 관련 질문을 입력하세요. 예: VPN 연결 방법 알려줘")
if question:
    started = time.perf_counter()
    result = route_question(question, faq)
    elapsed = time.perf_counter() - started
    try:
        save_usage(employee_id, question, result, "text", elapsed)
        st.session_state.last_log_status = "✓ 최근 사용 기록이 DB에 즉시 저장되었습니다."
    except Exception as exc:
        st.session_state.last_log_status = f"⚠ 로그 저장 실패: {type(exc).__name__}"
    add_exchange(question, result)
    st.rerun()
