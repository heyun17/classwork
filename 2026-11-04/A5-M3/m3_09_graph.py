"""실습 09 · ontology.json → NetworkX 노드 · 엣지
사용 예) python m3_09_graph.py
        python m3_09_graph.py --node POL-RET-002     # 노드 하나의 선 모두 보기
"""
import argparse
import json
from collections import Counter

import networkx as nx

from m3lib import OUT, load_graph

ap = argparse.ArgumentParser()
ap.add_argument("--node")
a = ap.parse_args()
G = load_graph()

if a.node:
    print(f"[{a.node}] 종류 {G.nodes[a.node]['type']} · 나가는 선 {G.out_degree(a.node)} · 들어오는 선 {G.in_degree(a.node)}")
    for s, o, d in G.out_edges(a.node, data=True):
        print(f"  → ({s}, {d['predicate']}, {o})  · {d['section']}")
    for s, o, d in G.in_edges(a.node, data=True):
        print(f"  ← ({s}, {d['predicate']}, {o})  · {d['doc_id']} · {d['section']}")
    raise SystemExit

print(f"그래프 · 스키마 {G.graph['schema_version']} · 노드 {G.number_of_nodes()}개 · 엣지 {G.number_of_edges()}개\n")
print("노드 종류:", ", ".join(f"{t} {c}" for t, c in Counter(nx.get_node_attributes(G, "type").values()).most_common()))
print("엣지 관계:", ", ".join(f"{p} {c}" for p, c in Counter(k for _, _, k in G.edges(keys=True)).most_common()))

print("\n[연결이 많은 노드 10개] (들어오는 선 + 나가는 선)")
for n, d in sorted(G.degree, key=lambda x: -x[1])[:10]:
    print(f"  {n:<14} {G.nodes[n]['type']:<6} {d:>3}  (나감 {G.out_degree(n)}, 들어옴 {G.in_degree(n)})")

U = G.to_undirected()
parts = sorted(nx.connected_components(U), key=len, reverse=True)
print(f"\n[이어진 덩어리] {len(parts)}개 · 가장 큰 덩어리 노드 {len(parts[0])}개")
for p in parts[1:]:
    print("  떨어진 덩어리:", ", ".join(sorted(p)))
alone = [n for n in G if G.nodes[n]["type"] == "정책" and not any(k == "함께적용" for *_, k in G.in_edges(n, keys=True)) and not any(k == "함께적용" for *_, k in G.out_edges(n, keys=True))]
print(f"\n[함께적용 선이 하나도 없는 정책] {len(alone)}개: {', '.join(sorted(alone))}")

OUT.mkdir(exist_ok=True)
data = nx.node_link_data(G, edges="edges")
(OUT / "graph.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n저장: outputs_m3/graph.json")
