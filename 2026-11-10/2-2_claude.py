import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# .env 파일 로드 (스크립트와 같은 폴더 또는 상위 폴더에서 탐색)
load_dotenv()

PDF_PATH = "000660_SK_2023.pdf"
INDEX_PATH = "faiss_sk_esg"
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")

# API 키 확인 (없으면 친절한 메시지 출력 후 종료)
if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit(
        "OPENAI_API_KEY가 설정되지 않았습니다.\n"
        "스크립트와 같은 폴더에 .env 파일을 만들고 아래 한 줄을 추가하세요:\n"
        "OPENAI_API_KEY=sk-여기에_본인_키"
    )

embeddings = OpenAIEmbeddings(model=EMBED_MODEL)

# 인덱스가 이미 있으면 재사용, 없으면 PDF로부터 생성
if os.path.exists(INDEX_PATH):
    vectorstore = FAISS.load_local(
        INDEX_PATH, embeddings, allow_dangerous_deserialization=True
    )
else:
    docs = PyPDFLoader(PDF_PATH).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_PATH)

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

prompt = ChatPromptTemplate.from_template(
    """아래 문서 내용만 근거로 질문에 한국어로 답하세요.
문서에 없는 내용이면 "문서에서 찾을 수 없습니다"라고 답하세요.

[문서]
{context}

[질문]
{question}"""
)

llm = ChatOpenAI(model=LLM_MODEL, temperature=0)


def format_docs(docs):
    return "\n\n".join(
        f"(p.{d.metadata.get('page', 0) + 1}) {d.page_content}" for d in docs
    )


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

if __name__ == "__main__":
    question = "SK주식회사의 4대 핵심 투자 영역과 각 영역별 누적 투자 금액은?"
    print(rag_chain.invoke(question))