"""
step07 · 도구 2 · 가명처리 도구

실행: 랭스미스 폴더에서  python 따라하기/step07.py
"""

import hashlib
import json
import os
import re
from datetime import datetime

from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, MessagesState, StateGraph

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


AGENT_PROMPT = """너는 병원 데이터 담당자를 돕는 '보건의료 가명처리 도우미'야. 다음 순서를 지켜.
1. 사용자가 밝힌 활용 목적이 가이드라인상 가명정보 활용 목적(통계작성, 과학적 연구, 공익적 기록보존)에
   해당하는지 search_guideline으로 근거를 찾아 확인해.
   - 해당하지 않으면 가명처리를 하지 말고, 가이드라인 근거(쪽 번호)와 함께 이유를 설명해.
2. 허용 목적이면 pseudonymize로 기록을 가명처리하고, 결과(가명정보, 처리내역)를 보여줘."""


agent = create_agent(model=llm, tools=[search_guideline, pseudonymize], system_prompt=AGENT_PROMPT)


# ─────────────────────────────────────────────
# 3. 그래프
# ─────────────────────────────────────────────


class State(MessagesState):                           # messages(대화 기록) + context 칸
    context: str


def last_user_text(state: State) -> str:
    return state["messages"][-1].content


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
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

graph = builder.compile()


if __name__ == "__main__":
    # ① 도구만 따로 실행해 보기 (LLM 없이)
    record = {"이름": "홍길동", "주민번호": "900101-1234567", "환자번호": "H-20231",
              "전화번호": "010-1234-5678", "진단": "제2형 당뇨", "HbA1c": "7.8"}
    print(json.dumps(pseudonymize.invoke({"record": record}), ensure_ascii=False, indent=2))

    # ② 에이전트에게 맡겨 보기
    result = agent.invoke({"messages": [{"role": "user", "content":
        "당뇨 치료제 효과를 비교하는 연구에 쓰려고 해. 이 기록을 가명처리해줘. "
        "이름: 홍길동, 주민번호: 900101-1234567, 환자번호: H-20231, 전화번호: 010-1234-5678, "
        "진단: 제2형 당뇨, HbA1c: 7.8"}]})
    print("\n[에이전트 답변]\n" + result["messages"][-1].content)
