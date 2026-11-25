"""실습 18 · Vector RAG vs GraphRAG vs Hybrid vs Auto — 평가 하네스
지표: Recall@k(찾은 정답/전체 정답) · Precision@k · Hit@1(1위가 정답) · MRR(첫 정답 순위의 역수 평균) · 지연(ms)
사용 예) python m5_18_compare.py                  # 네 방법 비교 + outputs_m5/eval_report.csv
        python m5_18_compare.py --by-type         # 질문 유형별 Recall@5
        python m5_18_compare.py --wins            # 방법마다 결과가 다른 질문
        python m5_18_compare.py --save-baseline   # 지금 결과를 기준선으로 저장
        python m5_18_compare.py --check           # 기준선보다 나빠졌으면 실패(종료 코드 1) — 배포 전 회귀 테스트
        python m5_18_compare.py --check --disable "날짜가 있는 질문"   # 규칙 하나를 끄면?
"""
import argparse
import csv
import json
import time
from collections import defaultdict

from m3lib import ROOT
from m5lib import load_questions, question_vectors, recall
from m5_retriever import Retriever

ap = argparse.ArgumentParser()
ap.add_argument("-k", type=int, default=5)
ap.add_argument("--by-type", action="store_true")
ap.add_argument("--wins", action="store_true")
ap.add_argument("--save-baseline", action="store_true")
ap.add_argument("--check", action="store_true")
ap.add_argument("--disable", nargs="*", default=[], help="끌 규칙 이름 (예: '날짜가 있는 질문')")
a = ap.parse_args()
K = a.k
QS = load_questions()
QV, _ = question_vectors(QS)
M = ("vector", "graph", "hybrid", "auto")
rows = []
for m in M:
    R = Retriever(m, K, disabled=a.disable)
    for i, q in enumerate(QS):
        t0 = time.perf_counter()
        res = R.search(q["question"], QV[i])
        ms = (time.perf_counter() - t0) * 1000
        got = [r["doc_id"] for r in res["results"]]
        first = next((n for n, d in enumerate(got, 1) if d in q["expected"]), None)
        rows.append({"method": m, "qid": q["id"], "type": q["type"], "expected": len(q["expected"]), "found": recall(q["expected"], got),
                     "returned": len(got), "hit1": int(bool(got) and got[0] in q["expected"]), "rr": 1 / first if first else 0,
                     "route": res["route"], "rules": "|".join(res["rules_fired"]), "ms": ms, "results": "|".join(got)})

out = ROOT / "outputs_m5" / "eval_report.csv"
out.parent.mkdir(exist_ok=True)
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


def summary(m):
    r = [x for x in rows if x["method"] == m]
    tot = sum(x["expected"] for x in r)
    return {"recall": sum(x["found"] for x in r) / tot, "found": sum(x["found"] for x in r), "total": tot,
            "precision": sum(x["found"] for x in r) / sum(x["returned"] for x in r), "hit1": sum(x["hit1"] for x in r) / len(r),
            "mrr": sum(x["rr"] for x in r) / len(r), "ms": sum(x["ms"] for x in r) / len(r)}


if a.by_type:
    agg = defaultdict(lambda: defaultdict(int))
    for x in rows:
        agg[x["type"]][x["method"]] += x["found"]
        if x["method"] == "vector":
            agg[x["type"]]["tot"] += x["expected"]
            agg[x["type"]]["n"] += 1
    print(f"질문 유형별 Recall@{K}\n")
    print(f"{'유형':<18}{'질문':>4}" + "".join(f"{m:>9}" for m in M))
    for t, v in sorted(agg.items()):
        total = v["tot"]
        print(f"{t:<18}{v['n']:>4}" + "".join(f"{f'{v[m]}/{total}':>9}" for m in M))
    raise SystemExit

if a.wins:
    by = defaultdict(dict)
    for x in rows:
        by[x["qid"]][x["method"]] = x
    print(f"방법마다 찾은 정답 수가 다른 질문 (상위 {K})\n")
    print(f"{'질문':<7}{'유형':<18}{'정답':>4}" + "".join(f"{m:>8}" for m in M) + "   auto 경로 · 규칙")
    for qid, d in by.items():
        h = [d[m]["found"] for m in M]
        if len(set(h)) > 1:
            print(f"{qid:<7}{d['vector']['type']:<18}{d['vector']['expected']:>4}" + "".join(f"{x:>8}" for x in h) + f"   {d['auto']['route']} · {d['auto']['rules'] or '-'}")
    raise SystemExit

S = {m: summary(m) for m in M}
print(f"평가 질문 {len(QS)}개 · 상위 {K} · 정답 정책 합계 {S['vector']['total']}개\n")
print(f"{'방법':<9}{'Recall':>12}{'Precision':>11}{'Hit@1':>8}{'MRR':>7}{'지연(ms)':>10}")
for m in M:
    s = S[m]
    print(f"{m:<9}{s['found']:>5}/{s['total']} {s['recall']:.2f}{s['precision']:>11.2f}{s['hit1']:>8.2f}{s['mrr']:>7.2f}{s['ms']:>10.1f}")
print(f"\n질문별 결과: outputs_m5/eval_report.csv ({len(rows)}행)")

base = ROOT / "design" / "m5_baseline.json"
if a.save_baseline:
    base.write_text(json.dumps({"k": K, "metrics": {m: {x: round(S[m][x], 4) for x in ("recall", "precision", "hit1", "mrr")} for m in M}}, indent=2), encoding="utf-8")
    print(f"기준선 저장: design/m5_baseline.json")
if a.check:
    b = json.loads(base.read_text(encoding="utf-8"))["metrics"]
    bad = []
    print("\n기준선과 비교 (auto)")
    for x in ("recall", "precision", "hit1", "mrr"):
        now, was = round(S["auto"][x], 4), b["auto"][x]
        mark = "▲" if now > was else ("▼" if now < was else "=")
        print(f"  {x:<10}{was:.3f} → {now:.3f} {mark}")
        if now < was:
            bad.append(x)
    if bad:
        print(f"실패: {', '.join(bad)} 이(가) 기준선보다 낮습니다")
        raise SystemExit(1)
    print("통과")
