"""A5-M3 실습 공통 코드 — ontology.json을 NetworkX 그래프로 다룬다."""
import json
import re
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs_m3"
COLORS = {"정책": "#6366f1", "상품유형": "#10b981", "지역": "#f59e0b", "회원등급": "#ec4899",
          "주문상태": "#14b8a6", "처리": "#ef4444", "사유": "#8b5cf6", "확인항목": "#9ca3af"}


def load_graph(path="outputs_m2/ontology.json"):
    """노드에는 종류(type)를, 선에는 관계 이름과 근거(doc_id, section, evidence)를 붙인다."""
    onto = json.loads((ROOT / path).read_text(encoding="utf-8"))
    G = nx.MultiDiGraph(schema_version=onto["schema_version"])
    for n in onto["nodes"]:
        G.add_node(n["id"], type=n["type"])
    for e in onto["edges"]:
        G.add_edge(e["subject"], e["object"], key=e["predicate"], predicate=e["predicate"],
                   doc_id=e["doc_id"], section=e["section"], evidence=e["evidence"])
    return G


def policies(G, nodes):
    return [n for n in nodes if G.nodes[n].get("type") == "정책"]


def start_nodes(G, question):
    """질문 속 말 → 그래프 노드. 노드 이름이 그대로 나오거나, 동의어 표에 있으면 출발점."""
    syn = json.loads((ROOT / "design" / "m3_synonyms.json").read_text(encoding="utf-8"))
    q = re.sub(r"\s+", "", question)
    found = {}
    for n in G.nodes:
        if G.nodes[n]["type"] not in ("정책", "확인항목") and n in q:
            found[n] = n
    for word, node in syn.items():
        if not word.startswith("_") and re.sub(r"\s+", "", word) in q and node not in found:
            found[node] = word
    return {n: w for n, w in found.items() if n in G}, {n: w for n, w in found.items() if n not in G}


def hop_search(G, starts, hops=2):
    """1홉: 출발 개념에 닿은 정책 (점수 = 닿은 출발 개념 수). 2홉: 그 정책에서 '함께적용'으로 이어진 정책."""
    U = G.to_undirected(as_view=True)
    score, via = {}, {}
    for s in starts:
        for p in policies(G, U.neighbors(s)):
            score[p] = score.get(p, 0) + 1
            via.setdefault(p, []).append(s)
    hop1 = sorted(score, key=lambda p: (-score[p], p))
    hop2 = []
    if hops >= 2:
        for p in hop1:
            for a, b, k in list(G.out_edges(p, keys=True)) + list(G.in_edges(p, keys=True)):
                other = b if a == p else a
                if k == "함께적용" and other not in score and other not in hop2:
                    hop2.append(other)
                    via[other] = [f"{p} (함께적용)"]
    return hop1, hop2, score, via
