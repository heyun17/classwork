"""실습 13 · FAISS HNSW 인덱스 — 그래프를 따라가며 가까운 조각 찾기
사용 예) python m4_13_hnsw.py
"""
import time

import faiss

from m4lib import build_embeddings, hit, load_chunks, questions, unit

E = build_embeddings()
X, Q, ids = unit(E["chunk_vecs"]), unit(E["q_vecs"]), E["chunk_ids"]
by_id = {c["chunk_id"]: c for c in load_chunks()}
K = 5
flat = faiss.IndexFlatIP(X.shape[1])
flat.add(X)
_, F = flat.search(Q, K)
tot = sum(len(q["expected"]) for q in questions())

print(f"{'방법':<26}{'만드는 시간(ms)':>14}{'Flat과 같은 결과':>16}{'정답 정책':>10}")
for M in (4, 16, 32):
    for ef in (8, 32, 128):
        t0 = time.perf_counter()
        h = faiss.IndexHNSWFlat(X.shape[1], M, faiss.METRIC_INNER_PRODUCT)
        h.hnsw.efConstruction = 40
        h.add(X)
        build = (time.perf_counter() - t0) * 1000
        h.hnsw.efSearch = ef
        _, I = h.search(Q, K)
        same = sum(len(set(I[i]) & set(F[i])) for i in range(len(Q)))
        got = sum(hit(q["expected"], [by_id[ids[j]]["doc_id"] for j in I[i] if j >= 0]) for i, q in enumerate(questions()))
        print(f"{f'HNSW M={M} efSearch={ef}':<26}{build:>14.1f}{f'{same}/{len(Q) * K}':>16}{f'{got}/{tot}':>10}")
print("\nM = 노드마다 잇는 이웃 수 · efSearch = 검색할 때 살펴보는 후보 수")
print("조각이 196개뿐이라 시간 차이는 작다. 수십만 개가 되면 Flat은 느려지고 IVF · HNSW가 필요해진다.")
