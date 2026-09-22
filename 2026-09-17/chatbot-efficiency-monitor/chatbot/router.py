import re
import pandas as pd

SECURITY_WORDS = {
    "관리자 권한",
    "root",
    "비밀번호 알려",
    "보안 해제",
    "방화벽 해제",
    "접근 권한",
}

# 업무 외 차단은 매우 보수적으로 적용한다.
# '월급', '구내식당', '인터넷', '날씨'처럼 업무 맥락일 수 있는 단어는 여기 넣지 않는다.
# 아래처럼 명백한 잡담/놀이 요청만 API 호출 전에 차단한다.
NON_WORK_PATTERNS = (
    r"^(나\s*)?심심(해|하다|한데|해요|합니다)?$",
    r"^(나랑\s*)?놀자$",
    r"^(너\s*)?(지금\s*)?뭐해$",
    r"^(재밌는|웃긴)\s*(얘기|이야기)(\s*(해줘|들려줘))?$",
    r"^끝말잇기(\s*하자)?$",
    r"^농담(\s*(하나\s*)?해줘)?$",
    r"^나랑\s*(대화해|대화하자|얘기하자)$",
)


def _norm(text: str) -> str:
    q = re.sub(r"\s+", " ", (text or "").strip().lower())
    # 문장 끝의 가벼운 구두점 때문에 잡담 탐지가 실패하지 않도록 정리한다.
    return re.sub(r"[?.!~]+$", "", q).strip()


def _is_obvious_non_work(q: str) -> bool:
    return any(re.fullmatch(pattern, q) for pattern in NON_WORK_PATTERNS)


def menu_answer(menu_id: str, faq_df: pd.DataFrame) -> dict:
    row = faq_df[faq_df["menu_id"] == menu_id]
    if row.empty:
        return {
            "route": "UNKNOWN_MENU",
            "answer": "등록되지 않은 메뉴입니다.",
            "use_api": False,
            "anomaly": False,
            "department": "미분류",
            "category": "미분류",
        }

    item = row.iloc[0]
    if item["sensitivity"] == "restricted":
        return {
            "route": "SECURITY_ESCALATE",
            "answer": str(item["answer"]),
            "use_api": False,
            "anomaly": False,
            "department": str(item["department"]),
            "category": str(item["category"]),
        }

    return {
        "route": "MENU_FAQ",
        "answer": str(item["answer"]),
        "use_api": False,
        "anomaly": False,
        "department": str(item["department"]),
        "category": str(item["category"]),
    }


def route_question(question: str, faq_df: pd.DataFrame) -> dict:
    q = _norm(question)
    if not q:
        return {
            "route": "EMPTY",
            "answer": "질문을 입력해주세요.",
            "use_api": False,
            "anomaly": False,
            "department": "미분류",
            "category": "미분류",
        }

    # 1. 보안/권한 요청은 LLM에 보내지 않고 담당자 절차로 안내한다.
    if any(word in q for word in SECURITY_WORDS):
        return {
            "route": "SECURITY_ESCALATE",
            "answer": "보안 또는 권한 관련 요청은 챗봇이 직접 처리하지 않습니다. 사내 권한신청 절차 또는 담당자에게 문의하세요.",
            "use_api": False,
            "anomaly": False,
            "department": "보안",
            "category": "권한/보안",
        }

    # 2. 자주 묻는 질문은 키워드 FAQ로 먼저 처리한다.
    #    월급/급여처럼 충분히 사내 업무 문의가 될 수 있는 표현도 FAQ에서 처리한다.
    best = None
    best_score = 0
    for _, row in faq_df.iterrows():
        kws = [k.strip().lower() for k in str(row["keywords"]).split(",") if k.strip()]
        score = sum(1 for k in kws if k in q)
        if score > best_score:
            best_score = score
            best = row

    if best is not None and best_score > 0:
        if best["sensitivity"] == "restricted":
            return {
                "route": "SECURITY_ESCALATE",
                "answer": str(best["answer"]),
                "use_api": False,
                "anomaly": False,
                "department": str(best["department"]),
                "category": str(best["category"]),
            }
        return {
            "route": "TEXT_FAQ",
            "answer": str(best["answer"]),
            "use_api": False,
            "anomaly": False,
            "department": str(best["department"]),
            "category": str(best["category"]),
        }

    # 3. 명백한 잡담/놀이 요청만 업무 외 질문으로 차단한다.
    if _is_obvious_non_work(q):
        return {
            "route": "NON_WORK",
            "answer": "사내 업무 지원용 챗봇입니다. 업무와 무관한 잡담이나 놀이 요청에는 답변하지 않습니다.",
            "use_api": False,
            "anomaly": True,
            "department": "미분류",
            "category": "명백한 잡담",
        }

    # 4. 그 밖의 질문은 업무 가능성을 열어두고 AI 처리 단계로 전달한다.
    #    예: 월급 상세 문의, 구내식당 메뉴, 인터넷 장애, 복지/규정 질문 등.
    return {
        "route": "LLM_REQUIRED",
        "answer": "등록된 FAQ만으로는 바로 답변하기 어려운 질문입니다. 실제 운영에서는 사내 문서 검색 또는 AI 답변 단계로 전달합니다. 데모에서는 실제 API를 호출하지 않습니다.",
        "use_api": True,
        "anomaly": False,
        "department": "미분류",
        "category": "AI 업무문의",
    }
