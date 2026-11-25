"""실습 20 · 테스트 질문으로 검색 점검 — 여러 정책 · 메타 누락 · 정책 충돌 · 접근 제한 · 검색 실패
테스트 질문 11개(design/m6_tests.json)는 평가 질문에 없던 새 질문이라 임베딩이 먼저 필요하다.
사용 예) python m6_20_tests.py --dry-run        # 무엇을 임베딩할지만 (API 없음)
        python m6_20_tests.py --embed          # 새 질문만 임베딩해 캐시에 저장 (API 한 번)
        python m6_20_tests.py                  # 점검표
        python m6_20_tests.py --detail T-06    # 한 질문의 결과 자세히
        python m6_20_tests.py --min-score 0.45 # 검색 실패 기준 바꿔 보기
"""
import argparse
import csv

import m6lib
from m3lib import ROOT
from m4lib import embed_with_cache

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--embed", action="store_true")
ap.add_argument("--detail")
ap.add_argument("--min-score", type=float)
a = ap.parse_args()
T = m6lib.tests()

_, st = embed_with_cache([t["question"] for t in T], apply=False)
if a.dry_run or (st["miss"] and not a.embed):
    print(f"테스트 질문 {st['total']}개 · 캐시에 있음 {st['hit']}개 · 새로 임베딩할 것 {len(st['miss'])}개")
    for i in st["miss"]:
        print(f"   - {T[i]['id']}  {T[i]['question']}")
    if st["miss"] and not a.dry_run:
        print("\n먼저 python m6_20_tests.py --embed  (새 질문만 API로 임베딩)")
    raise SystemExit
if a.min_score is not None:
    m6lib.MIN_SCORE = a.min_score

res, st = m6lib.retrieve(T, apply=a.embed)
if a.embed:
    print(f"임베딩: 새로 {len(st['miss'])}개 · 토큰 {st['tokens']}\n")


def check(t, r):
    docs = [x["doc_id"] for x in r["results"]]
    why = []
    miss = [d for d in t.get("expect_docs", []) if d not in docs]
    if miss and not t.get("no_evidence"):
        why.append("빠짐 " + ",".join(miss))
    if t.get("first") and docs[:1] != [t["first"]]:
        why.append(f"1위가 {docs[0]} (기대 {t['first']})")
    if t.get("not_first") and docs[:1] == [t["not_first"]]:
        why.append(f"1위가 {t['not_first']} (안 됨)")
    if t.get("flag") and t["flag"] not in r["flags"]:
        why.append(f"{t['flag']} 플래그 없음")
    if t.get("no_evidence") and not r["no_evidence"]:
        why.append(f"검색 실패로 판정 못 함 (점수 {r['top_score']})")
    if not t.get("no_evidence") and r["no_evidence"]:
        why.append(f"근거 있는데 실패로 판정 (점수 {r['top_score']})")
    return docs, why


rows = []
print(f"검색 실패 기준: 가장 가까운 정책 점수 < {m6lib.MIN_SCORE} 이고 발동한 규칙이 없으면 '근거 없음'\n")
print(f"{'ID':<5} {'종류':<7} {'경로':<6} {'점수':>5}  {'판정':<4} 상위 5 정책 / 이유")
for t, r in zip(T, res):
    docs, why = check(t, r)
    flag = ("restricted " if "restricted" in r["flags"] else "") + ("근거없음" if r["no_evidence"] else "")
    print(f"{t['id']:<5} {t['kind']:<7} {r['route']:<6} {r['top_score']:>5}  {'통과' if not why else '실패':<4} {' '.join(docs)}  {flag}")
    if why:
        print(f"{'':<34}→ {' · '.join(why)}")
    rows.append({"id": t["id"], "kind": t["kind"], "route": r["route"], "top_score": r["top_score"], "no_evidence": r["no_evidence"],
                 "flags": "|".join(r["flags"]), "rules": "|".join(r["rules_fired"]), "results": "|".join(docs), "pass": not why, "why": " · ".join(why)})
ok = sum(x["pass"] for x in rows)
print(f"\n통과 {ok}/{len(rows)}")

print("\n[정책 충돌 — 같은 것을 버전마다 다르게 정한 곳 (design/m6_tests.json conflicts)]")
for c in m6lib.T["conflicts"]:
    print(f"  {c['what']:<18} v1(9월) {c['v1']:<10} {c['v1_doc']:<12} v2(10월~) {c['v2']:<10} {c['v2_doc']}")
print("  → 날짜가 있는 질문은 1위 정책이 그 날짜의 버전이어야 한다 (T-06: EXC-007 1위, T-07: EXC-007이 1위면 안 됨)")

out = ROOT / "outputs_m6"
out.mkdir(exist_ok=True)
with open(out / "test_report.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"\n저장: outputs_m6/test_report.csv")

if a.detail:
    t, r = next((t, r) for t, r in zip(T, res) if t["id"] == a.detail)
    print(f"\n[{t['id']}] {t['question']}")
    print(f"  경로 {r['route']} · 규칙 {r['rules_fired']} · 플래그 {r['flags']} · 출발 개념 {r['graph_starts']} · 그래프에 없는 개념 {r['graph_missing']}")
    print(f"  가장 가까운 정책 점수 {r['top_score']} · 근거 없음 {r['no_evidence']}")
    for x in r["results"]:
        ev = x["evidence"][0]
        print(f"  {x['rank']}. {x['doc_id']:<12} {x['title']:<22} {' · '.join(x['sources'] + x['rules'])}")
        print(f"       {ev['chunk_id']} {ev['section']} · 유사도 {ev['score']}")
