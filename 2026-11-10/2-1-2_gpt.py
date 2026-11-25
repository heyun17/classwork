
import os
import re
import pymupdf as fitz
from pathlib import Path
from itertools import permutations
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_faiss import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


# 0. 환경 설정
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

pdf_path = BASE_DIR / "000660_SK_2023.pdf"

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF 파일 없음: {pdf_path}")

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(".env에 OPENAI_API_KEY가 없습니다.")


# 1. 좌표 기반 도표 추출
def extract_portfolio_chart(page):
    # 이 SK 보고서에서 확인할 4개 투자 영역
    names = ("첨단소재", "그린", "바이오", "디지털")

    labels = {}
    amounts = []

    # 텍스트와 좌표를 함께 추출
    for block in page.get_text("blocks"):
        if block[6] != 0:  # 이미지 블록 제외
            continue

        text = block[4].strip()
        rect = fitz.Rect(block[:4])

        # 투자 영역의 이름과 위치
        if text in names and rect.x0 < page.rect.width / 2:
            labels[text] = rect

        # 금액과 위치 (예: 3.9조원)
        cleaned = re.sub(r"\s+", "", text)
        match = re.fullmatch(r"(\d+(?:\.\d+)?)조원", cleaned)

        # PDF 7페이지 왼쪽 투자 영역 도표 범위
        if match and rect.x0 < page.rect.width / 2:
            if 200 <= rect.y0 <= 650:
                amounts.append((match.group(1), rect))

    # 정확히 네 영역과 네 금액이 발견됐는지 확인
    if len(labels) != 4 or len(amounts) != 4:
        raise ValueError(
            f"도표 추출 실패: 영역 {len(labels)}개, "
            f"금액 {len(amounts)}개"
        )

    # 좌표상 거리가 최소인 1:1 대응 관계 선택
    def distance_sum(pairs):
        return sum(
            (labels[name].x0 - rect.x0) ** 2
            + (labels[name].y0 - rect.y0) ** 2
            for name, (_, rect) in zip(names, pairs)
        )

    best = min(permutations(amounts), key=distance_sum)

    investment = {
        name: amount
        for name, (amount, _) in zip(names, best)
    }

    total = round(sum(float(v) for v in investment.values()), 1)

    # 영역과 금액이 연결된 구조화 텍스트 생성
    content = "SK주식회사 4대 핵심 투자 영역별 누적 투자 금액\n"
    content += "기준: 2022년까지 누적 투자 금액\n"

    for name, amount in investment.items():
        content += f"{name}: {amount}조원\n"

    content += f"총 누적 투자 금액: {total}조원"

    return Document(
        page_content=content,
        metadata={"page": 6, "kind": "coordinate_chart"}
    )


# 2. PDF 전체 로딩
docs = []

with fitz.open(pdf_path) as pdf:
    page_count = len(pdf)

    for page_number, page in enumerate(pdf):
        text = page.get_text("text", sort=True)

        if text.strip():
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "page": page_number,
                        "kind": "text"
                    }
                )
            )

    # PDF 7페이지의 도표를 좌표 기반으로 재구성
    chart_doc = extract_portfolio_chart(pdf[6])
    docs.append(chart_doc)

print(f"PDF 로딩: {page_count}페이지")

print("\n[좌표 기반 도표 추출]")
print(chart_doc.page_content)


# 3. 텍스트 분할
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200
)

chunks = splitter.split_documents(docs)
print(f"\n청크 생성: {len(chunks)}개")


# 4. 임베딩 + FAISS
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

db = FAISS.from_documents(chunks, embeddings)


# 5. 유사 문서 검색
question = "SK주식회사의 4대 핵심 투자 영역과 각 영역별 누적 투자 금액은?"

results = db.similarity_search(question, k=4)

# 검색된 자료에 7페이지가 있다면,
# 좌표로 재구성한 도표를 우선 근거로 추가
if any(doc.metadata.get("page") == 6 for doc in results):
    results = [chart_doc] + [
        doc for doc in results
        if doc.metadata.get("kind") != "coordinate_chart"
    ]

context = "\n\n".join(
    f"[PDF {doc.metadata['page'] + 1}페이지]\n"
    f"{doc.page_content}"
    for doc in results
)


# 6. LLM 답변 생성
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)

response = llm.invoke([
    (
        "system",
        "제공된 PDF 문서만 근거로 한국어로 답변하세요. "
        "좌표 기반으로 재구성된 도표 정보가 있다면 "
        "그 항목과 금액의 대응 관계를 우선 사용하세요. "
        "매출액, 영업이익 등 다른 종류의 수치와 혼동하지 마세요. "
        "금액의 합계를 검산하세요. "
        "근거가 부족하면 임의로 추측하지 마세요."
    ),
    (
        "human",
        f"참고 문서:\n{context}\n\n질문: {question}"
    )
])

print("\n[LLM 답변]")
print(response.content)


# 7. 참고 페이지 출력
print("\n[참고 페이지]")

seen = set()

for doc in results:
    page = doc.metadata["page"] + 1

    if page not in seen:
        print(f"PDF {page}페이지")
        seen.add(page)
