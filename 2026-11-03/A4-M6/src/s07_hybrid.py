# ====================================================================
# Step 07 · Metadata 필터 + BM25 + Vector → outputs/hybrid_results.csv
# 흐름: 필터 → BM25 점수, Vector 점수 → 각각 0~1로 정규화(min-max) → 0.4·BM25 + 0.6·Vector
# ====================================================================
import csv
import time

import numpy as np

from config import OUT_DIR, CHUNK_METHODS, K_LIST, HYBRID_WEIGHTS
from common import load_golden, extract_filters, match_filters, to_doc_ranking
from s05_bm25 import bm25_scores
from s06_faiss import vector_scores


def _minmax(x):
    x = np.asarray(x, dtype="float64")
    return (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else np.zeros_like(x)


def hybrid_search(method, question, weights=HYBRID_WEIGHTS, use_filter=True):
    chunks, b = bm25_scores(method, question)
    _, v = vector_scores(method, question)
    filters = extract_filters(question) if use_filter else {}
    keep = [i for i, c in enumerate(chunks) if match_filters(c, filters)]
    if not keep:
        return []
    bn, vn = _minmax(b[keep]), _minmax(v[keep])          # 남은 후보끼리 정규화
    score = weights["bm25"] * bn + weights["vector"] * vn
    ranked = [dict(chunks[i], score=float(s), bm25_norm=float(x), vector_norm=float(y))
              for i, s, x, y in zip(keep, score, bn, vn)]
    return sorted(ranked, key=lambda c: -c["score"])


if __name__ == "__main__":
    rows = []
    for method in CHUNK_METHODS:
        for g in load_golden():
            t = time.perf_counter()
            ranked = hybrid_search(method, g["question"])
            ms = (time.perf_counter() - t) * 1000
            docs, used = to_doc_ranking(ranked, max(K_LIST))
            for r, (d, c) in enumerate(zip(docs, used), 1):
                rows.append({"retriever": "Hybrid", "chunk_method": method, "query_id": g["query_id"], "rank": r,
                             "doc_id": d, "chunk_id": c["chunk_id"], "score": round(c["score"], 4),
                             "bm25_norm": round(c["bm25_norm"], 3), "vector_norm": round(c["vector_norm"], 3),
                             "is_relevant": d in g["relevant_doc_ids"], "latency_ms": round(ms, 2)})
    with open(OUT_DIR / "hybrid_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("저장:", len(rows), "행 → outputs/hybrid_results.csv  | 가중치:", HYBRID_WEIGHTS)
