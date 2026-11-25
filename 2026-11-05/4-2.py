import json

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import CrossEncoder


# ==================================================
# 환경변수 / 설정
# ==================================================

load_dotenv()

eval_file = r"D:\OneDrive\#classes\November\1105\classwork\data\eval_set.json"
chroma_path = r"D:\OneDrive\#classes\November\1105\classwork\data\chroma_db"

COLLECTION_NAME = "travel_openai"
EMBED_MODEL = "text-embedding-3-small"
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
# 평가셋 불러오기
# ==================================================

with open(eval_file, "r", encoding="utf-8") as f:
    eval_items = json.load(f)

single_items = [
    item
    for item in eval_items
    if item["type"] == "single"
]

print("===== 평가셋 =====")
print("전체 문항 수:", len(eval_items))
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
            "distance": distance
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

    return [
        {
            **hit,
            "rerank_score": float(score)
        }
        for hit, score in ranked
    ]


# ==================================================
# chunk_id → doc_id
#
# 같은 문서의 청크가 여러 개 있으면
# 문서 번호는 한 번만 사용
# ==================================================

def to_docs(hits):

    docs = []

    for hit in hits:
        doc_id = hit["chunk_id"].split("-")[0]

        if doc_id not in docs:
            docs.append(doc_id)

    return docs


# ==================================================
# Recall@4
# ==================================================

def recall_at_4(final_docs, gold_docs):

    return (
        len(set(final_docs) & set(gold_docs))
        / len(gold_docs)
    )


# ==================================================
# Reciprocal Rank
# ==================================================

def reciprocal_rank(final_docs, gold_docs):

    for rank, doc_id in enumerate(
        final_docs,
        start=1
    ):
        if doc_id in gold_docs:
            return 1 / rank

    return 0.0


# ==================================================
# 전체 평가
# ==================================================

results = []

print("\n===== 24문항 평가 시작 =====")

for item in single_items:

    question_id = item["id"]
    question = item["question"]
    gold_docs = item["gold_doc_ids"]

    # ----------------------------------------------
    # 1. 벡터 검색 상위 10개
    # ----------------------------------------------

    vector_candidates = search(
        question,
        k=CANDIDATE_K
    )

    # ----------------------------------------------
    # 2. 리랭킹 전
    # 벡터 검색 상위 4개
    # ----------------------------------------------

    vector_top4 = vector_candidates[:FINAL_K]

    vector_docs = to_docs(
        vector_top4
    )

    vector_recall = recall_at_4(
        vector_docs,
        gold_docs
    )

    vector_rr = reciprocal_rank(
        vector_docs,
        gold_docs
    )

    # ----------------------------------------------
    # 3. 리랭킹 후
    # ----------------------------------------------

    reranked = rerank(
        question,
        vector_candidates
    )

    rerank_top4 = reranked[:FINAL_K]

    rerank_docs = to_docs(
        rerank_top4
    )

    rerank_recall = recall_at_4(
        rerank_docs,
        gold_docs
    )

    rerank_rr = reciprocal_rank(
        rerank_docs,
        gold_docs
    )

    # ----------------------------------------------
    # 결과 저장
    # ----------------------------------------------

    results.append({
        "id": question_id,
        "question": question,
        "gold_docs": gold_docs,

        "vector_docs": vector_docs,
        "vector_recall": vector_recall,
        "vector_rr": vector_rr,

        "rerank_docs": rerank_docs,
        "rerank_recall": rerank_recall,
        "rerank_rr": rerank_rr
    })

    print(
        f"{question_id} | "
        f"벡터 Recall={vector_recall:.2f}, RR={vector_rr:.2f} | "
        f"리랭킹 Recall={rerank_recall:.2f}, RR={rerank_rr:.2f}"
    )


# ==================================================
# 평균
# ==================================================

n = len(results)

vector_recall_avg = sum(
    r["vector_recall"]
    for r in results
) / n

vector_mrr = sum(
    r["vector_rr"]
    for r in results
) / n

rerank_recall_avg = sum(
    r["rerank_recall"]
    for r in results
) / n

rerank_mrr = sum(
    r["rerank_rr"]
    for r in results
) / n


# ==================================================
# 최종 결과표
# ==================================================

print("\n\n===== 4-2 검색 평가 결과 =====")

print(
    f"{'설정':<28}"
    f"{'문항 수':<10}"
    f"{'Recall@4':<12}"
    f"{'MRR'}"
)

print(
    f"{'벡터 검색 (리랭킹 없음)':<28}"
    f"{n:<10}"
    f"{vector_recall_avg:<12.3f}"
    f"{vector_mrr:.3f}"
)

print(
    f"{'벡터 검색 + 리랭킹':<28}"
    f"{n:<10}"
    f"{rerank_recall_avg:<12.3f}"
    f"{rerank_mrr:.3f}"
)


# ==================================================
# 리랭킹 후에도 정답 문서를 못 찾은 질문
# ==================================================

failed_after_rerank = [
    r
    for r in results
    if r["rerank_recall"] < 1.0
]

print("\n===== 리랭킹 후에도 정답 문서를 모두 못 찾은 질문 =====")

if not failed_after_rerank:
    print("없음")

else:
    for r in failed_after_rerank:

        print("\n문항:", r["id"])
        print("질문:", r["question"])
        print("정답 문서:", r["gold_docs"])
        print("리랭킹 후 문서:", r["rerank_docs"])
        print(
            "Recall@4:",
            f"{r['rerank_recall']:.2f}"
        )