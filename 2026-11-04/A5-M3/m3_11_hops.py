"""실습 11 · Neighborhood와 Multi-hop 탐색
사용 예) python m3_11_hops.py                       # 질문 7개 · 설계한 정답과 비교
        python m3_11_hops.py --detail Q-001         # 한 질문의 출발점 · 1홉 · 2홉
        python m3_11_hops.py --neighbors 냉장식품     # 한 노드의 이웃
        python m3_11_hops.py --path 냉장식품 POL-FEE-001  # 두 노드 사이의 가장 짧은 경로
"""
import argparse
import json

import networkx as nx

from m3lib import ROOT, hop_search, load_graph, start_nodes

ap = argparse.ArgumentParser()
ap.add_argument("--detail")
ap.add_argument("--neighbors")
ap.add_argument("--path", nargs=2)
a = ap.parse_args()
G = load_graph()
U = G.to_undirected(as_view=True)

if a.neighbors:
    n = a.neighbors
    print(f"[{n}] ({G.nodes[n]['type']})의 이웃 {len(list(U.neighbors(n)))}개")
    for s, o, d in list(G.out_edges(n, data=True)) + list(G.in_edges(n, data=True)):
        print(f"  ({s}, {d['predicate']}, {o})  · 근거 {d['doc_id']} · {d['section']}")
    raise SystemExit
if a.path:
    s, t = a.path
    try:
        p = nx.shortest_path(U, s, t)
    except nx.NetworkXNoPath:
        raise SystemExit(f"{s}와 {t} 사이에 경로가 없습니다")
    print(f"{s} → {t} · {len(p) - 1}홉")
    for x, y in zip(p, p[1:]):
        k, d = next(iter(G.get_edge_data(x, y, default={}).items()), (None, None))
        if d is None:
            k, d = next(iter(G.get_edge_data(y, x).items()))
            print(f"  {x} ←{k}─ {y}   · {d['doc_id']} · {d['evidence'][:50]}")
        else:
            print(f"  {x} ─{k}→ {y}   · {d['doc_id']} · {d['evidence'][:50]}")
    raise SystemExit

QS = json.loads((ROOT / "design" / "answers.json").read_text(encoding="utf-8"))["questions"]
if a.detail:
    q = next(x for x in QS if x["id"] == a.detail)
    starts, missing = start_nodes(G, q["question"])
    hop1, hop2, score, via = hop_search(G, starts)
    exp = set(q["expected"])
    mark = lambda p: "정답" if p in exp else "    "
    print(f"{q['id']} {q['question']}\n찾아야 할 정책: {q['expected']}\n")
    print("출발점: " + ", ".join(f"{n}(질문의 '{w}')" for n, w in starts.items()))
    if missing:
        print("그래프에 없는 개념: " + ", ".join(f"{n}(질문의 '{w}')" for n, w in missing.items()))
    print("\n1홉 — 출발점에 닿은 정책 (점수 = 닿은 출발점 수)")
    for p in hop1:
        print(f"  {mark(p)} {p:<12} {score[p]}  ← {', '.join(via[p])}")
    print("2홉 — 1홉 정책에서 함께적용으로 이어진 정책")
    for p in hop2:
        print(f"  {mark(p)} {p:<12}    ← {via[p][0]}")
    got = set(hop1) | set(hop2)
    print(f"\n빠진 정책: {sorted(exp - got) or '없음'} · 모은 정책 {len(got)}개")
    raise SystemExit

print(f"그래프 · 스키마 {G.graph['schema_version']}\n")
print(f"{'질문':<7}{'정답 수':>5}{'1홉':>8}{'1홉+2홉':>10}{'모은 정책':>8}{'최고점만':>9}{'그 수':>5}  출발점")
t1 = t2 = tn = tot = tt = ttn = 0
for q in QS:
    starts, _ = start_nodes(G, q["question"])
    hop1, hop2, score, _ = hop_search(G, starts)
    exp = set(q["expected"])
    best = [p for p in hop1 if score[p] == max(score.values())] if score else []
    hb = len(exp & set(best))
    tt, ttn = tt + hb, ttn + len(best)
    h1 = len(exp & set(hop1))
    h2 = len(exp & (set(hop1) | set(hop2)))
    n = len(hop1) + len(hop2)
    t1, t2, tn, tot = t1 + h1, t2 + h2, tn + n, tot + len(exp)
    print(f"{q['id']:<7}{len(exp):>5}{f'{h1}/{len(exp)}':>10}{f'{h2}/{len(exp)}':>10}{n:>8}{f'{hb}/{len(exp)}':>10}{len(best):>5}  {', '.join(starts)}")
print(f"{'합계':<7}{tot:>5}{f'{t1}/{tot}':>10}{f'{t2}/{tot}':>10}{tn:>8}{f'{tt}/{tot}':>10}{ttn:>5}")
print("\n최고점만 = 1홉 정책 중 출발점에 가장 많이 닿은 것만 남긴 경우")
