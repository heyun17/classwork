import re

import chromadb
from dotenv import load_dotenv
from openai import OpenAI


# ==================================================
# 환경변수 / 설정
# ==================================================

load_dotenv()

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
# 프롬프트 읽기
# ==================================================

with open(prompt_file, "r", encoding="utf-8") as f:
    prompt_template = f.read()


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
# 검색 함수
#
# category=None  -> 전체 검색
# category="정책" -> 정책만 검색
# ==================================================

def search(question, k=10, category=None):

    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=[question]
    )

    question_embedding = [
        response.data[0].embedding
    ]

    query_args = {
        "query_embeddings": question_embedding,
        "n_results": k,
        "include": [
            "documents",
            "metadatas",
            "distances"
        ]
    }

    if category is not None:
        query_args["where"] = {
            "category": category
        }

    results = collection.query(**query_args)

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
# 답변 생성
# 검색 결과 상위 4개를 LLM에 전달
# ==================================================

def generate_answer(question, hits):

    top4 = hits[:4]

    context = "\n\n".join(
        f"[{hit['chunk_id']}] {hit['text']}"
        for hit in top4
    )

    prompt = prompt_template.format(
        question=question,
        context=context
    )

    response = openai_client.responses.create(
        model=CHAT_MODEL,
        input=prompt
    )

    return response.output_text


# ==================================================
# 출력
# ==================================================

def show(question, category=None):

    hits = search(
        question,
        k=10,
        category=category
    )

    if category is None:
        label = "필터 없음"
    else:
        label = f"category={category}"

    print(f"\n[{label}]")

    print("검색 상위 4개:")

    for rank, hit in enumerate(hits[:4], start=1):
        print(
            f"{rank}위 | "
            f"{hit['chunk_id']} | "
            f"[{hit['title']}] | "
            f"{hit['category']} | "
            f"distance: {hit['distance']:.4f}"
        )

    answer = generate_answer(
        question,
        hits
    )

    print("\n답변:")
    print(answer)


# ==================================================
# 비교 질문
# ==================================================

question = "파도소리 리조트는 체크인 며칠 전까지 취소하면 전액 환불되나요?"

print("===== 3-2 필터 적용 RAG 비교 =====")
print("질문:", question)

show(
    question,
    category=None
)

show(
    question,
    category="정책"
)

# ==================================================
# 규칙 적용 질문
# eval_set.json S24
# ==================================================

rule_question = "해온호스피탈리티 숙소를 체크인 5일 전에 취소하면 몇 %를 환불받나요?"

print("\n\n===== 규칙 적용 질문 =====")
print("질문:", rule_question)

rule_hits = search(
    rule_question,
    k=4,
    category="정책"
)

print("\n검색 상위 4개:")

for rank, hit in enumerate(rule_hits[:4], start=1):
    print(
        f"{rank}위 | "
        f"{hit['chunk_id']} | "
        f"[{hit['title']}] | "
        f"{hit['category']} | "
        f"distance: {hit['distance']:.4f}"
    )

print("\n검색 1위 청크 원문:")
print(rule_hits[0]["text"])

rule_answer = generate_answer(
    rule_question,
    rule_hits
)

print("\nLLM 답변:")
print(rule_answer)