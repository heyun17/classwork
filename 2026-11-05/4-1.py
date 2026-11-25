import re

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import CrossEncoder


# ==================================================
# 환경변수 / 설정
# ==================================================

load_dotenv()

chroma_path = r"D:\OneDrive\#classes\November\1105\classwork\data\chroma_db"

COLLECTION_NAME = "travel_openai"
EMBED_MODEL = "text-embedding-3-small"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

question = "바람결여행 상품은 언제까지 취소하면 전액 환불되나요?"


# ==================================================
# OpenAI / Chroma 연결
# ==================================================

openai_client = OpenAI()

chroma_client = chromadb.PersistentClient(
    path=chroma_path
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


# ==================================================
# 제목 추출
# ==================================================

def extract_title(text):
    if not text.startswith("["):
        return ""

    depth = 0

    for i, char in enumerate(text):
        if char == "[":
            depth += 1

        elif char == "]":
            depth -= 1

            if depth == 0:
                return text[1:i]

    return ""


# ==================================================
# 벡터 검색
# 상위 10개 후보
# ==================================================

def search(question, k=10):

    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=[question]
    )

    question_embedding = [
        response.data[0].embedding
    ]

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=k,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    hits = []

    for chunk_id, document, metadata, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):

        hits.append({
            "chunk_id": chunk_id,
            "title": extract_title(document),
            "text": document,
            "category": metadata["category"],
            "distance": distance
        })

    return hits


# ==================================================
# 1. 벡터 검색 상위 10개
# ==================================================

candidates = search(
    question,
    k=10
)

print("===== 4-1 리랭킹 =====")
print("질문:", question)

print("\n===== 리랭킹 전: 벡터 검색 상위 10개 =====")

for rank, hit in enumerate(candidates, start=1):

    print(
        f"{rank}위 | "
        f"{hit['chunk_id']} | "
        f"[{hit['title']}] | "
        f"{hit['category']} | "
        f"distance: {hit['distance']:.4f}"
    )


# ==================================================
# 2. Cross-Encoder 모델 불러오기
# ==================================================

print("\n===== 리랭커 모델 불러오기 =====")

reranker = CrossEncoder(
    RERANK_MODEL
)

print("모델:", RERANK_MODEL)


# ==================================================
# 3. 질문 + 청크를 한 쌍으로 점수 계산
# ==================================================

pairs = [
    (question, hit["text"])
    for hit in candidates
]

scores = reranker.predict(
    pairs
)


# ==================================================
# 4. 점수가 높은 순서로 재정렬
# ==================================================

ranked = sorted(
    zip(candidates, scores),
    key=lambda x: x[1],
    reverse=True
)


# ==================================================
# 5. 리랭킹 후 상위 4개
# ==================================================

print("\n===== 리랭킹 후 상위 4개 =====")

for new_rank, (hit, score) in enumerate(
    ranked[:4],
    start=1
):

    old_rank = next(
        i
        for i, candidate in enumerate(candidates, start=1)
        if candidate["chunk_id"] == hit["chunk_id"]
    )

    print(
        f"{new_rank}위 | "
        f"{hit['chunk_id']} | "
        f"[{hit['title']}] | "
        f"score: {float(score):.4f} | "
        f"{old_rank}위 → {new_rank}위"
    )


# ==================================================
# 6. 리랭킹 전 / 후 나란히 비교
# ==================================================

print("\n===== 리랭킹 전 / 후 비교 =====")

print(
    f"{'순위':<6}"
    f"{'리랭킹 전':<16}"
    f"{'리랭킹 후':<16}"
    f"{'점수'}"
)

for i, (hit, score) in enumerate(
    ranked[:4],
    start=1
):

    before_id = candidates[i - 1]["chunk_id"]

    print(
        f"{i:<6}"
        f"{before_id:<16}"
        f"{hit['chunk_id']:<16}"
        f"{float(score):.4f}"
    )