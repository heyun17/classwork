"""
step10 · 인터럽트 · 저장 전에 멈추기

실행: 랭스미스 폴더에서  python 따라하기/step10.py
"""

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command

# ─────────────────────────────────────────────
# 0. 환경설정
# ─────────────────────────────────────────────
load_dotenv()                                         # .env의 API 키를 읽어 옴
os.environ["LANGSMITH_PROJECT"] = "PARTB-guideline-agent"   # LangSmith 기록을 이 프로젝트에 모음

MODEL = "openai:" + (os.getenv("OPENAI_MODEL") or "gpt-4o-mini")
llm = init_chat_model(MODEL, temperature=0)


# ─────────────────────────────────────────────
# 1. RAG 자료 준비
# ─────────────────────────────────────────────
PDF_PATH = "가이드라인_발췌.pdf"                        # 랭스미스 폴더에서 실행하므로 파일 이름만 씀
pages = PyPDFLoader(PDF_PATH).load()                  # PDF 1쪽 = Document 1개

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(pages)              # 쪽 → 500자 조각 (메타데이터는 그대로 따라감)

vectorstore = InMemoryVectorStore(OpenAIEmbeddings(model="text-embedding-3-small"))
vectorstore.add_documents(chunks)                     # 조각마다 임베딩을 만들어 저장
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})   # 질문과 비슷한 조각 4개를 찾는 검색기


def format_docs(docs) -> str:
    """검색된 조각마다 [p.쪽번호]를 붙여 하나의 글로 합침"""
    return "\n\n---\n\n".join(
        f"[p.{d.metadata.get('page', 0) + 1}]\n{d.page_content}" for d in docs
    )


# ─────────────────────────────────────────────
# 2. 에이전트 도구
# ─────────────────────────────────────────────
@tool
def search_guideline(query: str) -> str:
    """보건의료데이터 활용 가이드라인에서 관련 내용을 검색한다.
    가명정보 활용 목적(통계작성, 과학적 연구, 공익적 기록보존)에 해당하는지,
    용어의 정의가 무엇인지 확인할 때 사용한다."""
    return format_docs(retriever.invoke(query))


# 가명처리에 쓰는 비밀값 = 가이드라인의 "추가정보". 실제로는 가명정보와 분리해서 보관해야 함
SALT = os.getenv("PSEUDO_SALT", "partb-demo-salt")


def _token(prefix: str, value: str) -> str:
    """같은 값은 항상 같은 가명으로 바뀌지만, SALT 없이는 원래 값을 알 수 없음"""
    return f"{prefix}-{hashlib.sha256((SALT + value).encode()).hexdigest()[:8]}"


def _age_group_and_sex(rrn: str) -> tuple[str, str]:
    """주민번호 → 연령대·성별로 일반화 (예: 900101-1234567 → 30대, 남)"""
    digits = re.sub(r"\D", "", rrn)
    yy, code = int(digits[:2]), digits[6]
    year = (1900 if code in "1256" else 2000) + yy
    age = datetime.now().year - year
    return f"{age // 10 * 10}대", ("남" if code in "1357" else "여")


@tool
def pseudonymize(record: dict) -> dict:
    """환자 기록 1건을 가명처리한다.
    record 예: {"이름": "홍길동", "주민번호": "900101-1234567", "환자번호": "H-20231",
               "전화번호": "010-1234-5678", "진단": "제2형 당뇨", "HbA1c": "7.8"}
    이름·환자번호는 가명ID로 대체, 주민번호는 연령대·성별로 일반화, 연락처·주소는 삭제한다."""
    result, log = {}, []
    for key, value in record.items():
        value = str(value)
        if key in ("이름", "성명"):
            result["가명ID"] = _token("P", value)
            log.append(f"{key}: 가명ID로 대체")
        elif key in ("주민번호", "주민등록번호"):
            result["연령대"], result["성별"] = _age_group_and_sex(value)
            log.append(f"{key}: 연령대·성별로 일반화 후 삭제")
        elif key in ("환자번호", "등록번호"):
            result[key] = _token("H", value)
            log.append(f"{key}: 가명번호로 대체")
        elif key in ("전화번호", "연락처", "주소", "이메일"):
            log.append(f"{key}: 삭제")
        else:
            result[key] = value                       # 진단·검사값은 분석에 필요하므로 유지
    return {
        "가명정보": result,
        "처리내역": log,
        "안내": "가명처리에 쓴 SALT(추가정보)는 가명정보와 분리해 보관해야 합니다.",
    }


OUT_DIR = Path("outputs")                             # 저장 폴더 (랭스미스/outputs)
# 저장 직전 마지막 안전장치: 주민번호·전화번호 패턴이 남아 있으면 저장 거부
_ID_PATTERNS = [r"\d{6}-?[1-8]\d{6}", r"01[016789]-?\d{3,4}-?\d{4}"]


@tool
def save_pseudonymized(data: dict, purpose: str) -> str:
    """가명처리된 데이터를 활용 목적과 함께 파일로 저장한다.
    반드시 pseudonymize 결과의 "가명정보"만 저장한다. 저장 전 담당자 승인이 필요하다."""
    text = json.dumps(data, ensure_ascii=False)
    if any(re.search(p, text) for p in _ID_PATTERNS):
        return "저장 거부: 주민번호나 전화번호로 보이는 식별정보가 남아 있습니다."
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"가명정보_{datetime.now():%Y%m%d_%H%M%S}.json"
    path.write_text(
        json.dumps({"활용목적": purpose, "저장시각": datetime.now().isoformat(), "데이터": data},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return f"저장 완료: outputs/{path.name} (활용목적: {purpose})"


AGENT_PROMPT = """너는 병원 데이터 담당자를 돕는 '보건의료 가명처리 도우미'야. 다음 순서를 지켜.
1. 사용자가 밝힌 활용 목적이 가이드라인상 가명정보 활용 목적(통계작성, 과학적 연구, 공익적 기록보존)에
   해당하는지 search_guideline으로 근거를 찾아 확인해.
   - 해당하지 않으면(예: 특정 개인 대상 1:1 마케팅) 가명처리·저장을 하지 말고, 가이드라인 근거(쪽 번호)와 함께 이유를 설명해.
   - 목적을 밝히지 않았으면 처리하지 말고 목적을 물어봐.
2. 허용 목적이면 pseudonymize로 기록을 가명처리해.
3. 이어서 바로 save_pseudonymized를 호출해 "가명정보"만 저장해. 담당자 승인은 호출하면 시스템이 받아 주니,
   승인을 기다리며 멈추지 말고 반드시 호출해.
4. 마지막에 확인한 근거(쪽 번호), 처리내역, 저장 결과를 한국어로 짧게 정리해."""


agent = create_agent(
    model=llm,
    tools=[search_guideline, pseudonymize, save_pseudonymized],
    system_prompt=AGENT_PROMPT,
    # ★ 인터럽트: save_pseudonymized를 실행하기 직전에 그래프가 멈추고 사람의 결정을 기다림
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "save_pseudonymized": {"allowed_decisions": ["approve", "edit", "reject"]},
            },
            description_prefix="가명정보 저장 승인 요청",
        )
    ],
    name="pseudonym_agent",
)


# ─────────────────────────────────────────────
# 3. 그래프
# ─────────────────────────────────────────────


class State(MessagesState):                           # messages(대화 기록) + route, context 칸
    route: str
    context: str


class RouteDecision(BaseModel):
    route: Literal["rag", "agent"] = Field(description="'rag' 또는 'agent'")


def last_user_text(state: State) -> str:
    return state["messages"][-1].content


def router(state: State):
    decision = llm.with_structured_output(RouteDecision).invoke(
        "다음 사용자 메시지를 분류해줘.\n"
        "- 'rag': 가이드라인 내용(용어 정의, 적용 범위, 활용 목적, 절차 등)을 묻는 질문\n"
        "- 'agent': 환자 기록 등 실제 데이터를 가명처리하거나 저장해 달라는 작업 요청\n"
        f"메시지: {last_user_text(state)}"
    )
    print(f"[router] → {decision.route}")
    return {"route": decision.route}


def retrieve(state: State):
    return {"context": format_docs(retriever.invoke(last_user_text(state)))}


def generate(state: State):
    prompt = (
        "아래 [가이드라인] 내용만 근거로 한국어로 답해줘. 문장 끝에 근거 쪽 번호를 (p.3)처럼 붙이고, "
        "가이드라인에 없는 내용이면 '가이드라인 발췌본에서 찾을 수 없습니다'라고 답해.\n\n"
        f"[가이드라인]\n{state['context']}\n\n[질문]\n{last_user_text(state)}"
    )
    return {"messages": [AIMessage(llm.invoke(prompt).content)]}


builder = StateGraph(State)
builder.add_node("router", router)
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.add_node("agent", agent)                      # 에이전트(작은 그래프)를 노드로 그대로 넣음
builder.add_edge(START, "router")
builder.add_conditional_edges("router", lambda s: s["route"], {"rag": "retrieve", "agent": "agent"})
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)
builder.add_edge("agent", END)

# 인터럽트로 멈췄다가 이어서 실행하려면 "어디까지 했는지" 저장해 둘 체크포인터가 필요함
graph = builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "step10"}}      # 같은 대화를 이어가기 위한 번호
    message = ("당뇨 치료제 효과를 비교하는 연구에 쓰려고 해. 이 환자 기록을 가명처리해서 저장해줘. "
           "이름: 홍길동, 주민번호: 900101-1234567, 환자번호: H-20231, 전화번호: 010-1234-5678, "
           "진단: 제2형 당뇨, HbA1c: 7.8")

    # ① 실행 → 저장 직전에 멈춤
    result = graph.invoke({"messages": [{"role": "user", "content": message}]}, config)
    request = result["__interrupt__"][0].value
    print("⏸  멈췄습니다! 승인 요청 내용:")
    for req in request["action_requests"]:
        print(" - 도구:", req["name"])
        print(" - 인자:", json.dumps(req["args"], ensure_ascii=False))

    # ② 승인하고 이어서 실행
    result = graph.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)
    print("\n[답변]\n" + result["messages"][-1].content)
