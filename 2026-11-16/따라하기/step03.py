"""
step03 · 벡터스토어에 저장하고 검색하기

실행: 랭스미스 폴더에서  python 따라하기/step03.py
"""

import os

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ─────────────────────────────────────────────
# 0. 환경설정
# ─────────────────────────────────────────────
load_dotenv()                                         # .env의 API 키를 읽어 옴
os.environ["LANGSMITH_PROJECT"] = "PARTB-guideline-agent"   # LangSmith 기록을 이 프로젝트에 모음


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


if __name__ == "__main__":
    question = "가명처리란 무엇인가요?"
    docs = retriever.invoke(question)
    print(f"질문: {question}  → 찾은 조각 {len(docs)}개\n")
    print(format_docs(docs)[:1200])
