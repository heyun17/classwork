import re

import chromadb
from dotenv import load_dotenv
from openai import OpenAI


# ==================================================
# 환경변수
# ==================================================

load_dotenv()


# ==================================================
# 설정
# ==================================================

chroma_path = r"D:\OneDrive\#classes\November\1105\classwork\data\chroma_db"

prompt_file = r"D:\OneDrive\#classes\November\1105\classwork\prompts\answer_v1.txt"

COLLECTION_NAME = "travel_openai"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-5.4-nano"


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
# 프롬프트 템플릿 읽기
# ==================================================

with open(prompt_file, "r", encoding="utf-8") as f:
    prompt_template = f.read()


# ==================================================
# 제목 추출
#
# document 형식:
# [제목] 본문...
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

            # 가장 바깥쪽 [ ]가 닫힌 지점
            if depth == 0:
                return text[1:i]

    return ""


# ==================================================
# 검색 함수
# 질문 → OpenAI 임베딩 → Chroma 상위 10개
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
# 프롬프트 만들기
# 검색 상위 4개만 LLM에 제공
# ==================================================

def build_prompt(question, hits):

    top4 = hits[:4]

    context = "\n\n".join(
        f"[{hit['chunk_id']}] {hit['text']}"
        for hit in top4
    )

    prompt = prompt_template.format(
        question=question,
        context=context
    )

    return prompt


# ==================================================
# 답변 생성
# ==================================================

def answer(question):

    hits = search(question, k=10)

    print("\n===== 검색 상위 4개 =====")
    print("질문:", question)
    print()

    for rank, hit in enumerate(hits[:4], start=1):

        print(
            f"{rank}위 | "
            f"{hit['chunk_id']} | "
            f"[{hit['title']}] | "
            f"{hit['category']} | "
            f"distance: {hit['distance']:.4f}"
        )

    prompt = build_prompt(
        question,
        hits
    )

    response = openai_client.responses.create(
        model=CHAT_MODEL,
        input=prompt
    )

    print("\n===== 답변 =====")
    print(response.output_text)

    return hits, response.output_text


# ==================================================
# 테스트 1
# 문서에 답이 있는 질문
# ==================================================

question1 = "노을스테이 호텔 옥상에서는 무엇을 할 수 있나요?"

print("\n\n########################################")
print("테스트 1 - 문서에 답이 있는 질문")
print("########################################")

answer(question1)


# ==================================================
# 테스트 2
# 문서에 없는 질문
# ==================================================

question2 = "솔바람섬에 공항이 있나요?"

print("\n\n########################################")
print("테스트 2 - 문서에 없는 질문")
print("########################################")

answer(question2)


# ==================================================
# 테스트 3
# 유사 명칭 질문
#
# 바람길여행 ↔ 바람결여행
# ==================================================

question3 = "바람결여행 상품은 언제까지 취소하면 전액 환불되나요?"

print("\n\n########################################")
print("테스트 3 - 유사 명칭 질문")
print("########################################")

answer(question3)