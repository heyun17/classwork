"""실습 08 · 스키마 버전별 ontology 비교
사용 예) python m2_08_compare.py                    # outputs_m2/ontology_v*.json 모두 나란히
        python m2_08_compare.py --concept 배송지연   # 한 개체에 닿는 선을 버전별로
"""
import argparse
import json
from collections import Counter

from m2lib import OUT

ap = argparse.ArgumentParser()
ap.add_argument("--versions", nargs="*", help="예: 0.1 0.3 (없으면 저장된 버전 모두)")
ap.add_argument("--concept")
a = ap.parse_args()
vers = a.versions or sorted(p.stem.split("_v")[1] for p in OUT.glob("ontology_v*.json"))
V = {v: json.loads((OUT / f"ontology_v{v}.json").read_text(encoding="utf-8")) for v in vers}

if a.concept:
    for v, o in V.items():
        es = [e for e in o["edges"] if a.concept in (e["subject"], e["object"])]
        print(f"[스키마 {v}] '{a.concept}'에 닿는 선 {len(es)}개")
        for e in es:
            print(f"   ({e['subject']}, {e['predicate']}, {e['object']})  · {e['doc_id']} · {e['section']}")
    raise SystemExit

rows = []
for v, o in V.items():
    rows.append((v, len(o["edges"]), len(o["rejected"]), len(o["nodes"]),
                 Counter(n["type"] for n in o["nodes"]), Counter(e["predicate"] for e in o["edges"])))
print(f"{'':<16}" + "".join(f"{'스키마 ' + r[0]:>12}" for r in rows))
print(f"{'저장한 선':<16}" + "".join(f"{r[1]:>12}" for r in rows))
print(f"{'버린 선':<16}" + "".join(f"{r[2]:>12}" for r in rows))
print(f"{'노드':<16}" + "".join(f"{r[3]:>12}" for r in rows))
types = sorted(set().union(*[r[4] for r in rows]), key=lambda t: -rows[-1][4][t])
for t in types:
    print(f"{'  노드 · ' + t:<16}" + "".join(f"{r[4][t]:>12}" for r in rows))
preds = sorted(set().union(*[r[5] for r in rows]), key=lambda p: -rows[-1][5][p])
for p in preds:
    print(f"{'  선 · ' + p:<16}" + "".join(f"{r[5][p]:>12}" for r in rows))
for v, o in V.items():
    named = [e for e in o["edges"] if e["predicate"] == "함께적용" and e["section"] != "확인 항목 및 주의"]
    print(f"\n[스키마 {v}] '적용 정책:' 줄이 아닌 곳에서 나온 함께적용 {len(named)}개")
    for e in named[:8]:
        print(f"   {e['subject']} → {e['object']}  · {e['section']} · {e['evidence'][:45]}")
    print(f"[스키마 {v}] 버린 이유: " + ", ".join(f"{r} {c}" for r, c in Counter(x["reason"] for x in o["rejected"]).most_common()))
