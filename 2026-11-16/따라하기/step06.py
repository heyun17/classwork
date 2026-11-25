"""
step06 · 도구 1 · 가이드라인 검색 도구와 에이전트

실행: 랭스미스 폴더에서  python 따라하기/step06.py
"""

import os

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


AGENT_PROMPT = """너는 병원 데이터 담당자를 돕는 '보건의료 가명처리 도우미'야.
질문에 답하기 전에 반드시 search_guideline으로 가이드라인 근거를 찾고, 근거 쪽 번호와 함께 답해."""


agent = create_agent(model=llm, tools=[search_guideline], system_prompt=AGENT_PROMPT)


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
    result = agent.invoke({"messages": [{"role": "user",
              "content": "신약 효과를 평가하는 연구도 가명정보 활용 목적에 해당해?"}]})
    for m in result["messages"]:                      # 에이전트가 주고받은 메시지를 모두 출력
        print(f"\n[{m.type}]", getattr(m, "tool_calls", "") or "", str(m.content)[:300])
