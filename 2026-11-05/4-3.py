import json
import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import CrossEncoder


# ==================================================
# 환경변수 / 경로 / 설정
# ==================================================

load_dotenv()

base_path = r"D:\OneDrive\#classes\November\1105\classwork"

eval_file = os.path.join(base_path, "data", "eval_set.json")
chroma_path = os.path.join(base_path, "data", "chroma_db")

answer_prompt_file = os.path.join(
    base_path,
    "prompts",
    "answer_v1.txt"
)

judge_prompt_file = os.path.join(
    base_path,
    "prompts",
    "judge_v1.txt"
)

result_file = os.path.join(
    base_path,
    "data",
    "4-3_results.json"
)


COLLECTION_NAME = "travel_openai"

EMBED_MODEL = "text-embedding-3-small"

# 과제2부터 사용한 답변 모델
ANSWER_MODEL = "gpt-5.4-nano"

# 참고문서 권장 채점 모델
JUDGE_MODEL = "gpt-5.4-mini"

RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

CANDIDATE_K = 10
FINAL_K = 4


# ==================================================
# OpenAI / Chroma
# ==================================================

openai_client = OpenAI()

chroma_client = chromadb.PersistentClient(
    path=chroma_path
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


# ==================================================
# 프롬프트 불러오기
# ==================================================

with open(
    answer_prompt_file,
    "r",
    encoding="utf-8"
) as f:
    answer_template = f.read()


with open(
    judge_prompt_file,
    "r",
    encoding="utf-8"
) as f:
    judge_template = f.read()


# ==================================================
# 평가셋
# ==================================================

with open(
    eval_file,
    "r",
    encoding="utf-8"
) as f:
    eval_items = json.load(f)


single_items = [
    item
    for item in eval_items
    if item["type"] == "single"
]


print("===== 평가셋 =====")
print("single 문항 수:", len(single_items))


# ==================================================
# 리랭커
# ==================================================

print("\n===== 리랭커 모델 불러오기 =====")

reranker = CrossEncoder(
    RERANK_MODEL
)

print("모델:", RERANK_MODEL)


# ==================================================
# 벡터 검색
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
            "text": document,
            "doc_id": metadata["doc_id"],
            "category": metadata["category"],
            "distance": float(distance)
        })

    return hits


# ==================================================
# 리랭킹
# ==================================================

def rerank(question, candidates):

    pairs = [
        (question, hit["text"])
        for hit in candidates
    ]

    scores = reranker.predict(
        pairs
    )

    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True
    )

    result = []

    for hit, score in ranked:

        new_hit = hit.copy()

        new_hit["rerank_score"] = float(
            score
        )

        result.append(
            new_hit
        )

    return result


# ==================================================
# context 만들기
# ==================================================

def build_context(hits):

    return "\n\n".join(
        f"[{hit['chunk_id']}] {hit['text']}"
        for hit in hits[:FINAL_K]
    )


# ==================================================
# 답변 생성
# ==================================================

def generate_answer(question, hits):

    context = build_context(
        hits
    )

    prompt = answer_template.format(
        question=question,
        context=context
    )

    response = openai_client.responses.create(
        model=ANSWER_MODEL,
        input=prompt
    )

    return (
        response.output_text,
        context
    )


# ==================================================
# LLM 채점
# ==================================================

def judge_answer(
    question,
    gold,
    answer,
    context
):

    prompt = judge_template.format(
        question=question,
        gold=gold,
        answer=answer,
        context=context
    )

    response = openai_client.responses.create(
        model=JUDGE_MODEL,
        input=prompt
    )

    raw = response.output_text.strip()

    try:
        score = json.loads(
            raw
        )

    except json.JSONDecodeError:
        print(
            "채점 JSON 파싱 실패:",
            raw[:200]
        )

        return {
            "correct": None,
            "faithful": None,
            "relevant": None,
            "reason": "JSON 파싱 실패",
            "raw": raw
        }

    return score


# ==================================================
# 기존 결과 있으면 불러오기
#
# 중간에 프로그램이 끊겨도
# 이미 처리한 문항은 다시 API 호출하지 않음
# ==================================================

if os.path.exists(result_file):

    with open(
        result_file,
        "r",
        encoding="utf-8"
    ) as f:

        saved_results = json.load(f)

else:
    saved_results = []


done_ids = {
    result["id"]
    for result in saved_results
}


results = saved_results


# ==================================================
# 24문항 답변 + 채점
# ==================================================

print("\n===== 4-3 답변 평가 시작 =====")


for index, item in enumerate(
    single_items,
    start=1
):

    question_id = item["id"]

    if question_id in done_ids:

        print(
            f"[{index}/24] "
            f"{question_id} 이미 완료 → 건너뜀"
        )

        continue


    question = item["question"]
    gold_answer = item["answer"]


    print(
        f"\n[{index}/24] "
        f"{question_id}"
    )

    print(
        "질문:",
        question
    )


    # ----------------------------------------------
    # 1. 벡터 검색 상위 10개
    # ----------------------------------------------

    candidates = search(
        question,
        k=CANDIDATE_K
    )


    # ----------------------------------------------
    # 2. 리랭킹 전 상위 4개
    # ----------------------------------------------

    vector_top4 = candidates[
        :FINAL_K
    ]

    vector_answer, vector_context = (
        generate_answer(
            question,
            vector_top4
        )
    )


    # ----------------------------------------------
    # 3. 리랭킹 전 답변 채점
    # ----------------------------------------------

    vector_score = judge_answer(
        question,
        gold_answer,
        vector_answer,
        vector_context
    )


    print(
        "벡터 검색:",
        vector_score
    )


    # ----------------------------------------------
    # 4. 리랭킹 후 상위 4개
    # ----------------------------------------------

    reranked = rerank(
        question,
        candidates
    )

    rerank_top4 = reranked[
        :FINAL_K
    ]


    # ----------------------------------------------
    # 5. 리랭킹 후 답변 생성
    # ----------------------------------------------

    rerank_answer, rerank_context = (
        generate_answer(
            question,
            rerank_top4
        )
    )


    # ----------------------------------------------
    # 6. 리랭킹 후 답변 채점
    # ----------------------------------------------

    rerank_score = judge_answer(
        question,
        gold_answer,
        rerank_answer,
        rerank_context
    )


    print(
        "리랭킹:",
        rerank_score
    )


    # ----------------------------------------------
    # 결과 저장
    # ----------------------------------------------

    result = {
        "id": question_id,
        "question": question,
        "gold_answer": gold_answer,

        "vector": {
            "chunk_ids": [
                hit["chunk_id"]
                for hit in vector_top4
            ],
            "context": vector_context,
            "answer": vector_answer,
            "score": vector_score
        },

        "rerank": {
            "chunk_ids": [
                hit["chunk_id"]
                for hit in rerank_top4
            ],
            "context": rerank_context,
            "answer": rerank_answer,
            "score": rerank_score
        }
    }


    results.append(
        result
    )


    # 문항 하나 끝날 때마다 저장
    with open(
        result_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )


# ==================================================
# JSON 파싱 성공한 결과만 평균 계산
# ==================================================

def valid_score(score):

    return (
        score.get("correct")
        in [0, 1]
        and score.get("faithful")
        in [0, 1]
        and score.get("relevant")
        in [0, 1]
    )


vector_scores = [
    result["vector"]["score"]
    for result in results
    if valid_score(
        result["vector"]["score"]
    )
]


rerank_scores = [
    result["rerank"]["score"]
    for result in results
    if valid_score(
        result["rerank"]["score"]
    )
]


# ==================================================
# 평균 함수
# ==================================================

def average(scores, key):

    if not scores:
        return 0.0

    return sum(
        score[key]
        for score in scores
    ) / len(scores)


# ==================================================
# 최종 결과
# ==================================================

print("\n\n===== 4-3 답변 평가 결과 =====")

print(
    f"{'설정':<28}"
    f"{'문항 수':<10}"
    f"{'정확도':<10}"
    f"{'Faithfulness':<16}"
    f"{'Relevancy'}"
)


print(
    f"{'벡터 검색 (리랭킹 없음)':<28}"
    f"{len(vector_scores):<10}"
    f"{average(vector_scores, 'correct'):<10.3f}"
    f"{average(vector_scores, 'faithful'):<16.3f}"
    f"{average(vector_scores, 'relevant'):.3f}"
)


print(
    f"{'벡터 검색 + 리랭킹':<28}"
    f"{len(rerank_scores):<10}"
    f"{average(rerank_scores, 'correct'):<10.3f}"
    f"{average(rerank_scores, 'faithful'):<16.3f}"
    f"{average(rerank_scores, 'relevant'):.3f}"
)


# ==================================================
# Faithfulness = 0 사례 출력
# ==================================================

print(
    "\n===== Faithfulness = 0 사례 ====="
)


faithfulness_failures = []


for result in results:

    if (
        result["vector"]["score"].get(
            "faithful"
        )
        == 0
    ):

        faithfulness_failures.append({
            "설정": "벡터 검색",
            "id": result["id"],
            "질문": result["question"],
            "답변": result["vector"]["answer"],
            "이유": result["vector"]["score"].get(
                "reason",
                ""
            )
        })


    if (
        result["rerank"]["score"].get(
            "faithful"
        )
        == 0
    ):

        faithfulness_failures.append({
            "설정": "리랭킹",
            "id": result["id"],
            "질문": result["question"],
            "답변": result["rerank"]["answer"],
            "이유": result["rerank"]["score"].get(
                "reason",
                ""
            )
        })


if not faithfulness_failures:

    print("없음")

else:

    for failure in faithfulness_failures:

        print(
            "\n설정:",
            failure["설정"]
        )

        print(
            "문항:",
            failure["id"]
        )

        print(
            "질문:",
            failure["질문"]
        )

        print(
            "답변:",
            failure["답변"]
        )

        print(
            "채점 이유:",
            failure["이유"]
        )


print(
    "\n결과 파일:",
    result_file
)