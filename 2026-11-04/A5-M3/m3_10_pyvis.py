"""실습 10 · PyVis로 그래프 그리기 (브라우저에서 끌고 클릭해 보는 HTML)
사용 예) python m3_10_pyvis.py                              # 전체 → outputs_m3/graph.html
        python m3_10_pyvis.py --focus EXC-001 --hops 2      # EXC-001에서 2홉까지 → graph_EXC-001_2.html
        python m3_10_pyvis.py --hide 확인항목                # 확인항목 노드 빼고 그리기
"""
import argparse

import networkx as nx
from pyvis.network import Network

from m3lib import COLORS, OUT, load_graph

ap = argparse.ArgumentParser()
ap.add_argument("--focus")
ap.add_argument("--hops", type=int, default=1)
ap.add_argument("--hide", nargs="*", default=[])
a = ap.parse_args()
G = load_graph()
if a.hide:
    G = G.subgraph([n for n in G if G.nodes[n]["type"] not in a.hide]).copy()
if a.focus:
    keep = nx.ego_graph(G.to_undirected(as_view=True), a.focus, radius=a.hops).nodes
    G = G.subgraph(keep).copy()

net = Network(height="760px", width="100%", directed=True, cdn_resources="in_line", bgcolor="#ffffff")
for n, d in G.nodes(data=True):
    size = 14 + 2 * G.degree(n) if d["type"] == "정책" else 10 + G.degree(n)
    net.add_node(n, label=n, color=COLORS.get(d["type"], "#999"), size=min(size, 45),
                 title=f"{n} · {d['type']} · 선 {G.degree(n)}개", shape="dot", font={"size": 22}, borderWidth=3 if n == a.focus else 1)
for s, o, d in G.edges(data=True):
    net.add_edge(s, o, label=d["predicate"], title=f"{d['doc_id']} · {d['section']}\n{d['evidence']}", arrows="to", color="#c7c9d1", font={"size": 14, "color": "#6b7280"})
net.barnes_hut(gravity=-6000, spring_length=140)
OUT.mkdir(exist_ok=True)
name = "graph" + (f"_{a.focus}_{a.hops}" if a.focus else "") + ("_hide" if a.hide else "") + ".html"
net.write_html(str(OUT / name), notebook=False)
print(f"노드 {G.number_of_nodes()}개 · 엣지 {G.number_of_edges()}개")
print("색: " + ", ".join(f"{t}={c}" for t, c in COLORS.items()))
print(f"저장: outputs_m3/{name}  (브라우저로 여세요. 선 위에 마우스를 올리면 근거 문장이 보입니다)")
