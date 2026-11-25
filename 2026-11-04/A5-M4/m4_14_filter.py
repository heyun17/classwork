"""실습 14 · 사전 필터와 사후 필터
- 사후 필터: 벡터로 상위 k개를 먼저 찾고, 조건에 맞지 않는 조각을 버린다 → k개보다 적게 남을 수 있다
- 사전 필터: 조건에 맞는 조각만 후보로 두고 그 안에서 상위 k개를 찾는다 (FAISS IDSelector)
사용 예) python m4_14_filter.py
        python m4_14_filter.py --detail Q-028
"""
import argparse

import faiss
import numpy as np

from m4lib import build_embeddings, hit, load_chunks, match, questions, unit

ap = argparse.ArgumentParser()
ap.add_argument("--detail")
ap.add_argument("-k", type=int, default=5)
a = ap.parse_args()
E = build_embeddings()
X, Q, ids = unit(E["chunk_vecs"]), unit(E["q_vecs"]), E["chunk_ids"]
chunks = {c["chunk_id"]: c for c in load_chunks()}
flat = faiss.IndexFlatIP(X.shape[1])
flat.add(X)
K = a.k


def vector(i, k=K):
    D, I = flat.search(Q[i:i + 1], k)
    return [(ids[j], float(d)) for j, d in zip(I[0], D[0])]


def post(i, cond):
    return [(c, d) for c, d in vector(i) if match(chunks[c]["meta"], cond)]


def pre(i, cond):
    allow = np.array([n for n, c in enumerate(ids) if match(chunks[c]["meta"], cond)], dtype="int64")
    params = faiss.SearchParameters(sel=faiss.IDSelectorBatch(allow))
    D, I = flat.search(Q[i:i + 1], K, params=params)
    return [(ids[j], float(d)) for j, d in zip(I[0], D[0]) if j >= 0], len(allow)


def show(rows, exp):
    for c, d in rows:
        m = chunks[c]["meta"]
        print(f"     {'정답' if chunks[c]['doc_id'] in exp else '    '} {c:<16}{d:.2f}  [{m['product_type']}/{m['region']}/{m['customer_grade']}] {chunks[c]['title']}")


QS = questions()
if a.detail:
    i, q = next((i, q) for i, q in enumerate(QS) if q["id"] == a.detail)
    print(f"{q['id']} {q['question']}\n조건 {q['conditions']} · 찾아야 할 정책 {q['expected']}\n")
    print(f"① 벡터만 상위 {K}"); show(vector(i), q["expected"])
    print(f"② 사후 필터 (상위 {K}개 중 조건에 맞는 것만)"); show(post(i, q["conditions"]), q["expected"])
    r, n = pre(i, q["conditions"])
    print(f"③ 사전 필터 (조건에 맞는 조각 {n}개 안에서 상위 {K})"); show(r, q["expected"])
    raise SystemExit

tot = sum(len(q["expected"]) for q in QS)
sv = spo = spr = n_post = 0
print(f"{'질문':<7}{'조건':<34}{'벡터만':>8}{'사후 필터':>10}{'남은 수':>6}{'사전 필터':>10}{'후보 조각':>8}")
for i, q in enumerate(QS):
    v, po = vector(i), post(i, q["conditions"])
    pr, n = pre(i, q["conditions"])
    e = len(q["expected"])
    hv, hpo, hpr = (hit(q["expected"], [chunks[c]["doc_id"] for c, _ in r]) for r in (v, po, pr))
    sv, spo, spr, n_post = sv + hv, spo + hpo, spr + hpr, n_post + len(po)
    cond = ", ".join(f"{k}={x}" for k, x in q["conditions"].items()) or "-"
    print(f"{q['id']:<7}{cond:<34}{f'{hv}/{e}':>8}{f'{hpo}/{e}':>10}{len(po):>6}{f'{hpr}/{e}':>10}{n:>8}")
print(f"{'합계':<41}{f'{sv}/{tot}':>8}{f'{spo}/{tot}':>10}{n_post:>6}{f'{spr}/{tot}':>10}")
print(f"\n사후 필터는 상위 {K}개 중 조건에 맞는 것만 남겨 질문당 {K}개보다 적어질 수 있다 (남은 수). 사전 필터는 늘 {K}개를 채운다.")
