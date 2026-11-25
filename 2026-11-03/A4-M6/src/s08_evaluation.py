# ====================================================================
# Step 08 · Golden Dataset 평가 → evaluation_summary / by_query / by_type / k_comparison / failure_cases / over_retrieved
# 결과 CSV(05·06·07)를 읽어서 계산만 한다 — 검색을 다시 돌리거나 Vector DB를 다시 만들지 않는다.
# ====================================================================
from collections import Counter

import pandas as pd

from config import OUT_DIR, K_LIST, DEFAULT_K, DEFAULT_CHUNK_METHOD
from common import (load_golden, load_chunks, precision_at_k, recall_at_k, hit_at_k,
                    reciprocal_rank, ndcg_at_k)

frames = [pd.read_csv(OUT_DIR / f) for f in ["bm25_results.csv", "vector_results.csv", "hybrid_results.csv"]
          if (OUT_DIR / f).exists()]
res = pd.concat(frames, ignore_index=True)
golden = {g["query_id"]: g for g in load_golden()}
size = {c["chunk_id"]: c["char_count"] for m in res["chunk_method"].unique() for c in load_chunks(m)}

per_query = []
for (ret, method, qid), grp in res.groupby(["retriever", "chunk_method", "query_id"]):
    grp = grp.sort_values("rank")
    ranked, rel, g = grp["doc_id"].tolist(), set(golden[qid]["relevant_doc_ids"]), golden[qid]
    scores = grp["score"].tolist()
    for k in K_LIST:
        per_query.append({
            "retriever": ret, "chunk_method": method, "K": k, "query_id": qid,
            "query_type": g["query_type"], "difficulty": g["difficulty"], "question": g["question"],
            "precision": precision_at_k(ranked, rel, k), "recall": recall_at_k(ranked, rel, k),
            "hit": hit_at_k(ranked, rel, k), "mrr": reciprocal_rank(ranked[:k], rel),
            "ndcg": ndcg_at_k(ranked, rel, k), "latency_ms": grp["latency_ms"].iloc[0],
            "context_chars": sum(size[c] for c in grp["chunk_id"].tolist()[:k]),
            "score_separation": (scores[0] - scores[1]) if len(scores) > 1 else 0,
            "top_k_docs": " > ".join(ranked[:k]), "relevant_docs": " , ".join(sorted(rel))})
pq = pd.DataFrame(per_query)
metrics = ["precision", "recall", "hit", "mrr", "ndcg", "latency_ms", "context_chars", "score_separation"]

summary = pq.groupby(["retriever", "chunk_method", "K"])[metrics].mean().round(3).reset_index()
summary.to_csv(OUT_DIR / "evaluation_summary.csv", index=False, encoding="utf-8-sig")

base = pq[(pq.chunk_method == DEFAULT_CHUNK_METHOD) & (pq.K == DEFAULT_K)]
base.to_csv(OUT_DIR / "evaluation_by_query.csv", index=False, encoding="utf-8-sig")
base.groupby(["retriever", "query_type"])[["precision", "recall", "hit", "mrr", "ndcg"]].mean().round(3) \
    .reset_index().to_csv(OUT_DIR / "evaluation_by_type.csv", index=False, encoding="utf-8-sig")
summary[summary.chunk_method == DEFAULT_CHUNK_METHOD].to_csv(OUT_DIR / "k_comparison.csv", index=False, encoding="utf-8-sig")
base[base.hit == 0].to_csv(OUT_DIR / "failure_cases.csv", index=False, encoding="utf-8-sig")

# 추가 모니터링: 정답 coverage, 너무 자주 검색되는 청크
cov = []
all_rel = {d for g in golden.values() for d in g["relevant_doc_ids"]}
for ret, grp in res[(res.chunk_method == DEFAULT_CHUNK_METHOD) & (res["rank"] <= DEFAULT_K)].groupby("retriever"):
    found = set(grp[grp.is_relevant]["doc_id"])
    top = Counter(grp["chunk_id"]).most_common(3)
    cov.append({"retriever": ret, "retrieval_coverage": round(len(found & all_rel) / len(all_rel), 3),
                "over_retrieved_top3": " | ".join(f"{c}({n})" for c, n in top)})
pd.DataFrame(cov).to_csv(OUT_DIR / "over_retrieved.csv", index=False, encoding="utf-8-sig")

pd.set_option("display.width", 160)
print(f"=== {DEFAULT_CHUNK_METHOD}, K={DEFAULT_K} ===")
print(summary[(summary.chunk_method == DEFAULT_CHUNK_METHOD) & (summary.K == DEFAULT_K)]
      [["retriever", "precision", "recall", "hit", "mrr", "ndcg", "latency_ms", "context_chars"]].to_string(index=False))
print("\n실패 질문(Hit@K=0):")
print(base[base.hit == 0][["retriever", "query_id", "query_type", "top_k_docs"]].to_string(index=False))
print("\n", pd.DataFrame(cov).to_string(index=False))
