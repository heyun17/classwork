"""실습 12 · OpenAI 임베딩 + FAISS IVF 인덱스
사용 예) python m4_12_ivf.py --dry-run     # 임베딩할 내용과 개수만 보기 (API 호출 없음)
        python m4_12_ivf.py               # 임베딩 만들기(처음 한 번) → Flat · IVF 검색 비교
"""
import argparse
import time

import faiss
import numpy as np

from m4lib import EMB, EMBED_MODEL, build_embeddings, hit, load_chunks, questions, unit

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--refresh", action="store_true")
ap.add_argument("--nlist", type=int, default=8)
ap.add_argument("-k", type=int, default=5)
a = ap.parse_args()
chunks = load_chunks()
by_id = {c["chunk_id"]: c for c in chunks}

if a.dry_run:
    n = sum(len(c["text"]) for c in chunks)
    print(f"모델 {EMBED_MODEL} · 조각 {len(chunks)}개 (글자 {n:,}) + 질문 {len(questions())}개를 임베딩합니다")
    for c in chunks[:2] + chunks[85:86]:
        print(f"\n[{c['chunk_id']}]\n{c['text'][:160]}")
    raise SystemExit

E = build_embeddings(a.refresh)
X = unit(E["chunk_vecs"])
Q = unit(E["q_vecs"])
ids = E["chunk_ids"]
print(f"임베딩: {E['info']['model']} · 조각 {X.shape[0]}개 × {X.shape[1]}차원 · 토큰 {E['info']['tokens']:,} · 저장 {EMB.name}\n")

# 정확한 검색 (모든 조각과 비교)
flat = faiss.IndexFlatIP(X.shape[1])
flat.add(X)

# IVF: 조각을 nlist개 묶음(클러스터)으로 나누고, 검색할 때 가까운 묶음 nprobe개만 본다
quant = faiss.IndexFlatIP(X.shape[1])
ivf = faiss.IndexIVFFlat(quant, X.shape[1], a.nlist, faiss.METRIC_INNER_PRODUCT)
ivf.train(X)
ivf.add(X)
sizes = np.bincount(ivf.quantizer.search(X, 1)[1].ravel(), minlength=a.nlist)
print(f"IVF 묶음 {a.nlist}개 · 묶음별 조각 수: {[int(x) for x in sizes]}\n")

_, F = flat.search(Q, a.k)
print(f"{'방법':<16}{'Flat과 같은 결과':>14}{'정답 정책':>10}{'시간(ms)':>10}")
rows = [("Flat (전부 비교)", flat, None)] + [(f"IVF nprobe={p}", ivf, p) for p in sorted({1, 2, 4, a.nlist})]
for name, idx, p in rows:
    if p:
        idx.nprobe = p
    t0 = time.perf_counter()
    _, I = idx.search(Q, a.k)
    ms = (time.perf_counter() - t0) * 1000
    same = sum(len(set(I[i]) & set(F[i])) for i in range(len(Q)))
    got = sum(hit(q["expected"], [by_id[ids[j]]["doc_id"] for j in I[i] if j >= 0]) for i, q in enumerate(questions()))
    tot = sum(len(q["expected"]) for q in questions())
    print(f"{name:<16}{f'{same}/{len(Q) * a.k}':>14}{f'{got}/{tot}':>10}{ms:>10.2f}")

print(f"\n[Flat 상위 {a.k}개 · 질문 7개]")
for i, q in enumerate(questions()):
    D, I = flat.search(Q[i:i + 1], a.k)
    docs = [by_id[ids[j]]["doc_id"] for j in I[0]]
    print(f"{q['id']} 정답 {hit(q['expected'], docs)}/{len(q['expected'])} · " + ", ".join(f"{ids[j]}({d:.2f})" for j, d in zip(I[0], D[0])))
faiss.write_index(ivf, str(EMB.parent / "ivf.index"))
print("\n저장: outputs_m4/ivf.index")
