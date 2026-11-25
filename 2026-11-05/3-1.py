import re
from collections import Counter

import chromadb
from dotenv import load_dotenv
from openai import OpenAI


# ==================================================
# 환경변수 / 설정
# ==================================================

load_dotenv()

chroma_path = r"D:\OneDrive\#classes\November\1105\classwork\data\chroma_db"

COLLECTION_NAME = "travel_openai"
EMBED_MODEL = "text-embedding-3-small"

question = "파도소리 리조트는 체크인 며칠 전까지 취소하면 전액 환불되나요?"


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
# 1. category 종류와 개수 확인
# ==================================================

stored = collection.get(
    include=["metadatas"]
)

category_counts = Counter(
    metadata["category"]
    for metadata in stored["metadatas"]
)

print("===== category별 청크 수 =====")

for category, count in category_counts.items():
    print(f"{category}: {count}개")


# ==================================================
# 질문 임베딩
# ==================================================

response = openai_client.embeddings.create(
    model=EMBED_MODEL,
    input=[question]
)

question_embedding = [
    response.data[0].embedding
]


# ==================================================
# 검색 함수
# ==================================================

def search(where=None):

    query_args = {
        "query_embeddings": question_embedding,
        "n_results": 5,
        "include": [
            "documents",
            "metadatas",
            "distances"
        ]
    }

    if where is not None:
        query_args["where"] = where

    return collection.query(**query_args)


# ==================================================
# 출력 함수
# ==================================================

def show_results(title, results):

    print(f"\n[{title}]")

    for rank, (
        chunk_id,
        document,
        metadata,
        distance
    ) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ),
        start=1
    ):

        doc_title = extract_title(document)

        print(
            f"{rank}위 | "
            f"{chunk_id} | "
            f"({metadata['category']}) | "
            f"[{doc_title}] | "
            f"distance: {distance:.4f}"
        )


# ==================================================
# 2. 필터 없음
# ==================================================

no_filter = search()


# ==================================================
# 3. category=정책
# ==================================================

policy_filter = search(
    where={"category": "정책"}
)


# ==================================================
# 4. 결과 비교
# ==================================================

print("\n\n===== 필터 검색 비교 =====")
print("질문:", question)

show_results(
    "필터 없음",
    no_filter
)

show_results(
    "필터 category=정책",
    policy_filter
)


# ==================================================
# 5. 여러 분류 허용
# 정책 + FAQ
# ==================================================

policy_faq_filter = search(
    where={
        "category": {
            "$in": ["정책", "FAQ"]
        }
    }
)

show_results(
    "필터 category=정책 또는 FAQ",
    policy_faq_filter
)