"""
step05 · RAG를 그래프로 감싸기

실행: 랭스미스 폴더에서  python 따라하기/step05.py
"""

import os

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import AIMessage
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
    print(graph.get_graph().draw_mermaid())
    result = graph.invoke({"messages": [{"role": "user", "content": "가명처리란 무엇인가요?"}]})
    print("[답변]\n" + result["messages"][-1].content)
