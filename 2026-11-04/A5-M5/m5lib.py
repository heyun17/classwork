"""A5-M5 실습 공통 코드 — 벡터 검색(M4)과 그래프 탐색(M3)을 정책 단위 순위로 맞춰 결합한다.

평가 질문: reference/evaluation_questions_30.csv (30개, 정답 정책 · 기대 관계 경로 포함)
질문 임베딩: m4lib의 캐시를 쓴다. 처음 한 번 `python m5_16_hybrid.py --embed`로 새 질문만 임베딩한다.
"""
import csv

import numpy as np

from m3lib import ROOT, hop_search, load_graph, start_nodes
from m4lib import build_embeddings, embed_with_cache, load_chunks, unit

G = load_graph()
E = build_embeddings()
X, IDS = unit(E["chunk_vecs"]), E["chunk_ids"]
CHUNKS = {c["chunk_id"]: c for c in load_chunks()}


def load_questions():
    rows = list(csv.DictReader(open(ROOT / "reference" / "evaluation_questions_30.csv", encoding="utf-8-sig")))
    return [{"id": r["question_id"], "question": r["question"], "type": r["scenario_type"],
             "expected": r["expected_doc_ids"].split("|"), "path": r["expected_relation_path"]} for r in rows]


def question_vectors(qs, apply=False):
    vecs, st = embed_with_cache([q["question"] for q in qs], apply=apply)
    if any(v is None for v in vecs):
        raise SystemExit(f"질문 {len(st['miss'])}개의 임베딩이 없습니다. 먼저 python m5_16_hybrid.py --embed (API 호출)")
    return unit(np.array(vecs, dtype="float32")), st


# ------------------------------------------------------------------ 세 가지 검색 (모두 정책 순위를 돌려준다)
def vector_rank(qv):
    """정책마다 가장 가까운 조각 점수로 순위 (M4 실습 15의 ②)"""
    s = X @ qv
    best = {}
    for j, v in enumerate(s):
        c = CHUNKS[IDS[j]]
        if c["kind"] == "policy" and float(v) > best.get(c["doc_id"], (-1,))[0]:
            best[c["doc_id"]] = (float(v), IDS[j])
    return sorted(best, key=lambda d: -best[d][0]), best


def graph_rank(question):
    """질문 속 개념 → 1홉(닿은 출발점 수 순) → 함께적용 2홉 (M3 실습 11)"""
    starts, missing = start_nodes(G, question)
    hop1, hop2, score, via = hop_search(G, starts)
    return hop1 + hop2, {"starts": starts, "missing": missing, "hop1": hop1, "hop2": hop2, "score": score, "via": via}


def rrf(*rankings, k=60):
    """Reciprocal Rank Fusion: 각 순위표에서 1/(k + 순위)를 더한다. 점수 단위가 달라도 순위만으로 합칠 수 있다."""
    s = {}
    for r in rankings:
        for i, d in enumerate(r, 1):
            s[d] = s.get(d, 0) + 1 / (k + i)
    return sorted(s, key=lambda d: -s[d]), s


def hybrid_rank(qv, question):
    v, _ = vector_rank(qv)
    g, _ = graph_rank(question)
    return rrf(v, g)[0]


def recall(expected, got):
    return len(set(expected) & set(got))
