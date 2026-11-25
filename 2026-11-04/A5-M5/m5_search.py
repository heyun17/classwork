"""검색기 사용 — 질문 하나를 넣으면 근거 패키지(JSON)를 돌려준다. 모든 호출은 outputs_m5/search_log.jsonl에 남는다.
사용 예) python m5_search.py --id Q-001                    # 평가 질문으로
        python m5_search.py --id Q-005 --method vector     # 방법 바꾸기
        python m5_search.py "제주 냉장식품이 늦게 왔어요"   # 새 질문 (처음 한 번 질문 임베딩 · API)
        python m5_search.py --id Q-023 --json              # 다른 프로그램에 넘길 JSON 그대로
"""
import argparse
import datetime
import json

from m4lib import OUT as OUT4  # noqa: F401
from m5lib import load_questions, question_vectors
from m5_retriever import Retriever
from m3lib import ROOT

ap = argparse.ArgumentParser()
ap.add_argument("question", nargs="?")
ap.add_argument("--id")
ap.add_argument("--method", default="auto", choices=["auto", "vector", "graph", "hybrid"])
ap.add_argument("-k", type=int, default=5)
ap.add_argument("--json", action="store_true")
a = ap.parse_args()

if a.id:
    q = next(x for x in load_questions() if x["id"] == a.id)
else:
    q = {"id": "NEW", "question": a.question, "expected": []}
qv, st = question_vectors([q], apply=True)
res = Retriever(a.method, a.k).search(q["question"], qv[0])
res["question_id"] = q["id"]

log = ROOT / "outputs_m5" / "search_log.jsonl"
log.parent.mkdir(exist_ok=True)
with open(log, "a", encoding="utf-8") as f:
    f.write(json.dumps({"time": datetime.datetime.now().isoformat(timespec="seconds"), "question_id": q["id"], "question": q["question"],
                        "method": res["method"], "route": res["route"], "rules": res["rules_fired"], "flags": res["flags"],
                        "results": [r["doc_id"] for r in res["results"]], "latency_ms": res["latency_ms"]}, ensure_ascii=False) + "\n")

if a.json:
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit
exp = set(q.get("expected", []))
print(f"{q['id']} {q['question']}")
print(f"방법 {res['method']} → 경로 {res['route']} · 규칙 {res['rules_fired'] or '없음'} · 표시 {res['flags'] or '없음'} · {res['latency_ms']}ms")
print(f"그래프 출발점 {res['graph_starts']}" + (f" · 그래프에 없는 개념 {res['graph_missing']}" if res["graph_missing"] else ""))
if exp:
    print(f"정답 {sorted(exp)}")
print()
for r in res["results"]:
    mark = "정답 " if r["doc_id"] in exp else ("     " if exp else "")
    why = " · ".join(r["sources"] + r["rules"]) or "-"
    print(f"{r['rank']}. {mark}{r['doc_id']} {r['title']}  ({why})")
    for e in r["evidence"][:1]:
        body = e["text"].split("\n", 1)[-1].replace("\n", " ")
        print(f"     근거 {e['chunk_id']} [{e['section']}] {body[:70]}")
    if r["path"]:
        print("     경로 " + " / ".join(p["edge"] for p in r["path"]))
