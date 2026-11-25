"""실무용 검색기 — 질문 하나를 받아 '정책 순위 + 근거 조각 + 그래프 경로 + 왜 골랐는지'를 돌려준다.

method
  vector  : 정책 단위 벡터 순위
  graph   : 질문 개념 → 그래프 1홉 · 2홉
  hybrid  : 두 순위를 RRF로 합침
  auto    : 규칙(design/m5_routing.json) → 그래프 출발점이 충분하면 hybrid, 아니면 vector
"""
import json
import re
import time

import networkx as nx

from m3lib import ROOT
from m5lib import CHUNKS, IDS, X, G, graph_rank, rrf, vector_rank

ROUTING = json.loads((ROOT / "design" / "m5_routing.json").read_text(encoding="utf-8"))
TITLES = {c["doc_id"]: c["title"] for c in CHUNKS.values() if c["kind"] == "policy"}
U = G.to_undirected(as_view=True)


def _path(starts, doc):
    best = None
    for s in starts:
        if doc in U and s in U and nx.has_path(U, s, doc):
            p = nx.shortest_path(U, s, doc)
            best = p if best is None or len(p) < len(best) else best
    if not best:
        return []
    out = []
    for x, y in zip(best, best[1:]):
        d = G.get_edge_data(x, y) or G.get_edge_data(y, x)
        k, v = next(iter(d.items()))
        arrow = f"{x} ─{k}→ {y}" if G.has_edge(x, y) else f"{x} ←{k}─ {y}"
        out.append({"edge": arrow, "doc_id": v["doc_id"], "section": v["section"], "evidence": v["evidence"]})
    return out


def _evidence(doc, qv, n=2, limit=300):
    """그 정책의 조각 중 질문과 가장 가까운 n개 (LLM에 넘길 근거)"""
    rows = [(float(X[j] @ qv), IDS[j]) for j in range(len(IDS)) if CHUNKS[IDS[j]]["doc_id"] == doc]
    rows.sort(reverse=True)
    return [{"chunk_id": c, "section": CHUNKS[c].get("section"), "score": round(s, 3), "text": CHUNKS[c]["text"][:limit]} for s, c in rows[:n]]


class Retriever:
    def __init__(self, method="auto", k=5, rrf_k=60, disabled=()):
        self.method, self.k, self.rrf_k, self.disabled = method, k, rrf_k, set(disabled)

    def search(self, question, qv):
        t0 = time.perf_counter()
        v, vs = vector_rank(qv)
        g, gi = graph_rank(question)
        fired = [r for r in ROUTING["rules"] if self.method == "auto" and r["name"] not in self.disabled and re.search(r["regex"], question)]
        method = self.method
        if method == "auto":
            method = "hybrid" if len(gi["starts"]) >= ROUTING["graph_min_starts"] else "vector"
        ranked = {"vector": v, "graph": g, "hybrid": rrf(v, g, k=self.rrf_k)[0]}[method]
        pin = [d for r in fired for d in r.get("pin", [])]
        add = [d for r in fired for d in r.get("add", []) if d not in pin]
        order = list(dict.fromkeys(pin + ranked[:2] + add + ranked[2:]))[: self.k]
        why = {d: [r["name"] + " · " + r["why"] for r in fired if d in r.get("pin", []) + r.get("add", [])] for d in order}
        results = []
        for rank, d in enumerate(order, 1):
            src = []
            if d in v[: self.k]:
                src.append(f"벡터 {v.index(d) + 1}위")
            if d in g[: self.k]:
                src.append(f"그래프 {g.index(d) + 1}위")
            results.append({"rank": rank, "doc_id": d, "title": TITLES.get(d, ""), "sources": src, "rules": why[d],
                            "path": _path(gi["starts"], d), "evidence": _evidence(d, qv)})
        return {"question": question, "method": self.method, "route": method,
                "rules_fired": [r["name"] for r in fired], "flags": sorted({r["flag"] for r in fired if "flag" in r}),
                "graph_starts": list(gi["starts"]), "graph_missing": list(gi["missing"]),
                "results": results, "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}
