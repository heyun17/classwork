# ====================================================================
# Step 05 · BM25 검색 → outputs/bm25_results.csv
# BM25: 질문과 '같은 단어'가 많이, 드물게 나오는 청크일수록 높은 점수 (A4-M2·M3의 match와 같은 원리)
# ====================================================================
import csv
import time

from rank_bm25 import BM25Okapi

from config import OUT_DIR, CHUNK_METHODS, K_LIST
from common import load_chunks, load_golden, tokenize, extract_filters, match_filters, to_doc_ranking

_cache = {}


def bm25_index(method):
    if method not in _cache:
        chunks = load_chunks(method)
        _cache[method] = (chunks, BM25Okapi([tokenize(c["content"]) for c in chunks]))
    return _cache[method]


def bm25_scores(method, question):
    chunks, bm = bm25_index(method)
    return chunks, bm.get_scores(tokenize(question))


def bm25_search(method, question, use_filter=False):
    """점수 순으로 정렬된 청크 목록(score 포함)을 돌려준다."""
    chunks, scores = bm25_scores(method, question)
    filters = extract_filters(question) if use_filter else {}
    ranked = [dict(c, score=float(s)) for c, s in zip(chunks, scores) if match_filters(c, filters)]
    return sorted(ranked, key=lambda c: -c["score"])


if __name__ == "__main__":
    rows = []
    for method in CHUNK_METHODS:
        for g in load_golden():
            for name, flt in [("BM25", False), ("Metadata+BM25", True)]:
                t = time.perf_counter()
                ranked = bm25_search(method, g["question"], flt)
                ms = (time.perf_counter() - t) * 1000
                docs, used = to_doc_ranking(ranked, max(K_LIST))
                for r, (d, c) in enumerate(zip(docs, used), 1):
                    rows.append({"retriever": name, "chunk_method": method, "query_id": g["query_id"],
                                 "rank": r, "doc_id": d, "chunk_id": c["chunk_id"], "score": round(c["score"], 4),
                                 "is_relevant": d in g["relevant_doc_ids"], "latency_ms": round(ms, 2)})
    with open(OUT_DIR / "bm25_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("저장:", len(rows), "행 → outputs/bm25_results.csv")
    for q in ["NB-SEOUL-26 제품 코드를 사용하는 문서는?", "2025년 부산 공공기관 노트북 전략을 찾아줘"]:
        print("\n질문:", q, "| 필터:", extract_filters(q))
        for name, flt in [("BM25", False), ("Metadata+BM25", True)]:
            docs, used = to_doc_ranking(bm25_search("heading", q, flt), 3)
            print(f"  {name:14}", [(d, round(c['score'], 2)) for d, c in zip(docs, used)])
