"""실습 17 · Multi-hop — 찾은 정책까지 몇 홉, 어떤 관계로 왔나
사용 예) python m5_17_multihop.py --detail Q-001   # 출발 개념 → 정답 정책 경로와 근거, 기대 관계 경로와 비교
        python m5_17_multihop.py                  # 30개 질문: 정답 정책이 몇 홉에서 처음 잡히나
"""
import argparse
from collections import Counter

import networkx as nx

from m5lib import G, graph_rank, load_questions, question_vectors, vector_rank

ap = argparse.ArgumentParser()
ap.add_argument("--detail")
a = ap.parse_args()
QS = load_questions()
QV, _ = question_vectors(QS)
U = G.to_undirected(as_view=True)


def edge_text(x, y):
    d = G.get_edge_data(x, y)
    if d:
        k, v = next(iter(d.items()))
        return f"{x} ─{k}→ {y}", v
    k, v = next(iter(G.get_edge_data(y, x).items()))
    return f"{x} ←{k}─ {y}", v


if a.detail:
    i, q = next((i, q) for i, q in enumerate(QS) if q["id"] == a.detail)
    _, gi = graph_rank(q["question"])
    print(f"{q['id']} {q['question']}\n기대 관계 경로(평가 자료): {q['path']}\n출발 개념: {', '.join(gi['starts'])}"
          + (f" · 그래프에 없는 개념: {', '.join(gi['missing'])}" if gi["missing"] else "") + "\n")
    for d in q["expected"]:
        best = None
        for s in gi["starts"]:
            if d in U and nx.has_path(U, s, d):
                p = nx.shortest_path(U, s, d)
                if best is None or len(p) < len(best):
                    best = p
        if not best:
            print(f"[{d}] 출발 개념에서 닿는 경로 없음\n")
            continue
        print(f"[{d}] {len(best) - 1}홉")
        for x, y in zip(best, best[1:]):
            t, v = edge_text(x, y)
            print(f"   {t:<40} · {v['doc_id']} · {v['section']} · {v['evidence'][:40]}")
        print()
    raise SystemExit

print("정답 정책이 처음 잡히는 단계 (30개 질문, 정답 정책 합계 기준)\n")
stage = Counter()
by_type = {}
for i, q in enumerate(QS):
    v, _ = vector_rank(QV[i])
    _, gi = graph_rank(q["question"])
    for d in q["expected"]:
        if d in v[:5]:
            s = "벡터 상위 5"
        elif d in gi["hop1"]:
            s = "그래프 1홉"
        elif d in gi["hop2"]:
            s = "그래프 2홉 (함께적용)"
        else:
            s = "못 찾음"
        stage[s] += 1
        by_type.setdefault(q["type"], Counter())[s] += 1
tot = sum(stage.values())
for s in ("벡터 상위 5", "그래프 1홉", "그래프 2홉 (함께적용)", "못 찾음"):
    print(f"  {s:<20}{stage[s]:>3} / {tot}")
print("\n질문 유형별")
for t, c in sorted(by_type.items()):
    print(f"  {t:<18}" + " · ".join(f"{s} {c[s]}" for s in ("벡터 상위 5", "그래프 1홉", "그래프 2홉 (함께적용)", "못 찾음") if c[s]))
