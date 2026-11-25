"""운영 2 · 인덱스에 추가 · 삭제 · 교체 (처음부터 다시 만들지 않기)
사용 예) python m4_ops_update.py
"""
import faiss
import numpy as np

from m4lib import build_embeddings, questions, unit

E = build_embeddings()
X, Q, ids = unit(E["chunk_vecs"]), unit(E["q_vecs"]), E["chunk_ids"]
num = np.arange(len(ids), dtype="int64")  # 조각마다 고정 번호
K = 5
qi = [q["id"] for q in questions()].index("Q-030")


def top(index):
    D, I = index.search(Q[qi:qi + 1], K)
    return [ids[j] for j in I[0] if j >= 0]


full = faiss.IndexIDMap2(faiss.IndexFlatIP(X.shape[1]))
full.add_with_ids(X, num)
print(f"[기준] 196개를 한 번에 넣은 인덱스 · Q-030 상위 {K}: {top(full)}\n")

new = np.array([i for i, c in enumerate(ids) if c.startswith("EXC-003")], dtype="int64")
old = np.array([i for i in num if i not in set(new)], dtype="int64")
idx = faiss.IndexIDMap2(faiss.IndexFlatIP(X.shape[1]))
idx.add_with_ids(X[old], old)
print(f"[1] EXC-003 조각 {len(new)}개를 빼고 {idx.ntotal}개로 시작 · Q-030 상위 {K}: {top(idx)}")
idx.add_with_ids(X[new], new)
print(f"[2] EXC-003 조각 {len(new)}개 추가 → {idx.ntotal}개 · Q-030 상위 {K}: {top(idx)}")
print(f"    기준과 같은가: {top(idx) == top(full)}")

target = ids.index("POL-FEE-001#5")
idx.remove_ids(np.array([target], dtype="int64"))
print(f"[3] POL-FEE-001#5 삭제 → {idx.ntotal}개 · Q-030 상위 {K}: {top(idx)}")
idx.add_with_ids(X[target:target + 1], np.array([target], dtype="int64"))
print(f"[4] 같은 번호로 다시 추가(교체) → {idx.ntotal}개 · 기준과 같은가: {top(idx) == top(full)}\n")

print("[인덱스 종류별로 되는 일]")
quant = faiss.IndexFlatIP(X.shape[1])
ivf = faiss.IndexIVFFlat(quant, X.shape[1], 4, faiss.METRIC_INNER_PRODUCT)
ivf.train(X[old])
ivf.add_with_ids(X[old], old)
ivf.add_with_ids(X[new], new)
print(f"  IVF : 추가 됨 ({ivf.ntotal}개) · 삭제 됨 ({ivf.remove_ids(np.array([target], dtype='int64'))}개) · 단, 묶음(centroid)은 처음 train한 데이터 기준 그대로")
h = faiss.IndexHNSWFlat(X.shape[1], 16, faiss.METRIC_INNER_PRODUCT)
h.add(X)
try:
    h.remove_ids(np.array([target], dtype="int64"))
    print("  HNSW: 삭제 됨")
except RuntimeError as e:
    print(f"  HNSW: 추가는 됨 · 삭제는 안 됨 → \"{str(e).split(': ')[-1].strip()}\"")
