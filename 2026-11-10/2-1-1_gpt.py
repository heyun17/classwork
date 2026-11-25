
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS

# 0. API 키 불러오기
load_dotenv(Path(__file__).with_name(".env"))

# 1. PDF 로딩
pdf_path = Path(__file__).with_name("000660_SK_2023.pdf")
docs = PyPDFLoader(str(pdf_path)).load()
print(f"PDF 로딩: {len(docs)}페이지")

# 2. 텍스트 분할 (Chunking)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(docs)
print(f"청크 생성: {len(chunks)}개")

# 3. 임베딩 모델
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 4. FAISS 벡터 DB 생성
db = FAISS.from_documents(chunks, embeddings)

# 5. 질문과 유사한 문서 검색 (Retrieval)
question = "SK주식회사의 4대 핵심 투자 영역과 각 영역별 누적 투자 금액은?"
results = db.similarity_search(question, k=3)

for i, doc in enumerate(results, 1):
    print(f"\n[검색 결과 {i}]")
    print(f"PDF 페이지: {doc.metadata['page'] + 1}")
    print(doc.page_content)

context = "\n\n".join(doc.page_content for doc in results)

# 6. 검색 결과로 LLM 답변 증강 (Generation)
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

response = llm.invoke([
    ("system", "제공된 문서 내용만 근거로 한국어로 답변하세요. 문서에 없는 내용은 모른다고 답하세요."),
    ("human", f"참고 문서:\n{context}\n\n질문: {question}")
])

print("\n[LLM 답변]")
print(response.content)

print("\n[참고 페이지]")
for doc in results:
    print(f"PDF {doc.metadata['page'] + 1}페이지")
