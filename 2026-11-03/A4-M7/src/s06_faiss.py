# ====================================================================
# Step 06 · 청킹 방식별 임베딩 + FAISS → outputs/faiss/<방식>/index.faiss, chunks.json, vector_results.csv
# 임베딩은 outputs/embedding_cache.json에 저장 — 같은 문장은 API를 다시 부르지 않는다.
# ====================================================================
import csv
import hashlib
import json
import time

import faiss
import numpy as np

from config import OUT_DIR, CHUNK_METHODS, K_LIST, EMBEDDING_MODEL, OPENAI_API_KEY, EMBED_BACKEND
from common import load_chunks, load_golden, to_doc_ranking

CACHE_PATH = OUT_DIR / "embedding_cache.json"
FAISS_DIR = OUT_DIR / "faiss"
_cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
_client = None


def _key(text):
    return hashlib.sha1(f"{EMBED_BACKEND}|{EMBEDDING_MODEL}|{text}".encode()).hexdigest()


def _fake(text, dim=256):
    rng = np.random.default_rng(int(hashlib.md5(text.encode()).hexdigest()[:8], 16))
    return rng.normal(size=dim).tolist()


def embed(texts):
    global _client
    todo = [t for t in texts if _key(t) not in _cache]
    if todo:
        if EMBED_BACKEND == "fake":
            for t in todo: _cache[_key(t)] = _fake(t)
        else:
            from openai import OpenAI
            _client = _client or OpenAI(api_key=OPENAI_API_KEY)
            for i in range(0, len(todo), 100):
                batch = todo[i:i + 100]
                resp = _client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
                for t, d in zip(batch, resp.data): _cache[_key(t)] = d.embedding
        CACHE_PATH.write_text(json.dumps(_cache), encoding="utf-8")
        if len(todo) > 1:
            print(f"  임베딩 새로 생성 {len(todo)}개 (캐시 총 {len(_cache)}개)")
    v = np.array([_cache[_key(t)] for t in texts], dtype="float32")
    faiss.normalize_L2(v)
    return v


def build_index(method):
    """청킹 방식이 바뀔 때만 다시 만든다. K·가중치를 바꿀 때는 부르지 않는다."""
    chunks = load_chunks(method)
    vecs = embed([c["content"] for c in chunks])
    index = faiss.IndexFlatIP(vecs.shape[1]); index.add(vecs)
    d = FAISS_DIR / method; d.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(d / "index.faiss"))
    (d / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return index, chunks


_loaded = {}


def load_index(method):
    if method not in _loaded:
        d = FAISS_DIR / method
        _loaded[method] = (faiss.read_index(str(d / "index.faiss")),
                           json.loads((d / "chunks.json").read_text(encoding="utf-8")))
    return _loaded[method]


def vector_scores(method, question):
    """모든 청크의 코사인 점수 (청크 순서 그대로)"""
    index, chunks = load_index(method)
    q = embed([question])
    scores, ids = index.search(q, index.ntotal)
    out = np.zeros(index.ntotal, dtype="float32"); out[ids[0]] = scores[0]
    return chunks, out


def vector_search(method, question):
    chunks, scores = vector_scores(method, question)
    return sorted([dict(c, score=float(s)) for c, s in zip(chunks, scores)], key=lambda c: -c["score"])


if __name__ == "__main__":
    for method in CHUNK_METHODS:
        index, chunks = build_index(method)
        print(f"{method}: 벡터 {index.ntotal}개, 차원 {index.d}")
    rows = []
    for method in CHUNK_METHODS:
        for g in load_golden():
            t = time.perf_counter()
            ranked = vector_search(method, g["question"])
            ms = (time.perf_counter() - t) * 1000
            docs, used = to_doc_ranking(ranked, max(K_LIST))
            for r, (d, c) in enumerate(zip(docs, used), 1):
                rows.append({"retriever": "Vector", "chunk_method": method, "query_id": g["query_id"], "rank": r,
                             "doc_id": d, "chunk_id": c["chunk_id"], "score": round(c["score"], 4),
                             "is_relevant": d in g["relevant_doc_ids"], "latency_ms": round(ms, 2)})
    with open(OUT_DIR / "vector_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("저장:", len(rows), "행 → outputs/vector_results.csv")
