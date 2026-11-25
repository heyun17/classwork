"""실습 21 · 답변 생성과 검증 — 검색 근거만으로 답하게 하고, 답을 세 가지로 검사한다
① 상태(answered · conditional · insufficient · refused)가 기대와 같은가
② 인용 검증: 인용 조각이 넘겨준 근거에 있고, 인용 문장이 원문 그대로이고, 답의 숫자가 인용 근거에 있는가
③ 꼭 들어가야 할 말(must_say)이 답에 있는가 — 예: 9월 VIP 기준 50000원, 10월 냉장식품 48시간
④ 버전 충돌: 날짜 규칙이 발동했는데 다른 버전의 값(design/m6_tests.json conflicts)을 말했는가
검색 실패(근거 없음)로 판정된 질문은 모델을 부르지 않고 바로 '근거 부족'으로 답한다.
사용 예) python m6_21_answer.py --dry-run --only T-06   # 보낼 지시문 보기 (API 없음)
        python m6_21_answer.py --qnum                  # 고객이 말한 숫자는 검사에서 빼기 (API 없음, 캐시)
        python m6_21_answer.py --qnum --rule-sections  # 규칙 정책의 업무 규정을 근거에 더해 다시 답하기 (API)
        python m6_21_answer.py                         # 테스트 11 + 평가 질문 5 (API, 결과는 캐시)
        python m6_21_answer.py --only T-06 --show      # 한 질문의 답 · 인용 · 검사 자세히
"""
import argparse
import csv
import json

import m6lib
from m3lib import ROOT
from rag_answer import answer, rule_sections, verify

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--only")
ap.add_argument("--show", action="store_true")
ap.add_argument("--refresh", action="store_true")
ap.add_argument("--qnum", action="store_true", help="질문에 있던 숫자는 근거에서 찾지 않기")
ap.add_argument("--rule-sections", action="store_true", help="규칙으로 고정된 정책의 '업무 규정' 조각을 근거에 더하기")
a = ap.parse_args()

EVAL_IDS = ["Q-001", "Q-003", "Q-005", "Q-023", "Q-030"]
items = m6lib.tests() + m6lib.eval_as_tests(EVAL_IDS)
if a.only:
    items = [t for t in items if t["id"] == a.only]
res, _ = m6lib.retrieve(items)

rows, shown = [], []
for t, r in zip(items, res):
    if r["no_evidence"]:
        rec = {"answer": "공개된 정책에서 이 질문의 근거를 찾지 못했습니다. 담당 부서 확인이 필요합니다.", "status": "insufficient", "citations": []}
        ctx, by = [], "검색 실패 → 모델 호출 안 함"
    else:
        extra = rule_sections(r) if a.rule_sections else None
        out, ctx, p = answer(t["question"], r, dry_run=a.dry_run, refresh=a.refresh, extra_ctx=extra)
        if out is None and not a.dry_run:
            print(f"[{t['id']}] 답이 캐시에 없습니다 — API로 새로 만들려면 키가 필요합니다"); continue
        if a.dry_run:
            print(f"[{t['id']}] 보낼 지시문\n{p}\n")
            continue
        rec, by = out["data"], "모델 답변"
    v = verify(rec, ctx, t["question"] if a.qnum else None) if ctx else {"ok": True, "citations": [], "numbers": []}
    st_ok = rec.get("status") in t["expect_status"]
    must = [w for w in t.get("must_say", []) if w.replace(",", "") not in rec.get("answer", "").replace(",", "")]
    why = []
    if not st_ok:
        why.append(f"상태 {rec.get('status')} (기대 {'/'.join(t['expect_status'])})")
    for c in v["citations"]:
        if not c["in_context"]:
            why.append(f"{c['chunk_id']} 근거 밖")
        elif not c["quote_found"]:
            why.append(f"{c['chunk_id']} 인용 불일치")
    why += [f"숫자 {x['value']} 근거에 없음" for x in v["numbers"] if not x["found"] and not (a.qnum and x.get("in_question"))]
    ver = "v1" if "9월 주문 → v1" in r["rules_fired"] else ("v2" if "날짜가 있는 질문" in r["rules_fired"] else None)
    clash = []
    if ver:
        for c in m6lib.T["conflicts"]:
            wrong = c["v2"] if ver == "v1" else c["v1"]
            if wrong.replace(",", "") in rec.get("answer", "").replace(",", "").replace(" ", ""):
                clash.append(f"버전 충돌: {c['what']} {wrong} (주문일 버전은 {ver})")
    why += clash
    why += [f"‘{w}’ 없음" for w in must]
    passed = st_ok and v["ok"] and not must and not clash
    rows.append({"id": t["id"], "kind": t["kind"], "status": rec.get("status"), "expect": "/".join(t["expect_status"]),
                 "citations": "|".join(c.get("chunk_id", "") for c in rec.get("citations", [])), "verify_ok": v["ok"],
                 "must_say_ok": not must, "version_ok": not clash, "pass": passed, "why": " · ".join(why), "by": by, "answer": rec.get("answer", "")})
    shown.append((t, r, rec, v, ctx))
if a.dry_run:
    raise SystemExit

print(f"{'ID':<6} {'종류':<9} {'상태':<12} {'인용검증':<6} {'must':<5} {'버전':<4} {'판정':<4} 이유")
for x in rows:
    print(f"{x['id']:<6} {x['kind']:<9} {x['status']:<12} {'OK' if x['verify_ok'] else '걸림':<6} {'OK' if x['must_say_ok'] else '없음':<5} {'OK' if x['version_ok'] else '충돌':<4} {'통과' if x['pass'] else '실패':<4} {x['why'] or '-'}")
n = len(rows)
print(f"\n상태 일치 {sum(x['why'].find('상태') < 0 for x in rows)}/{n} · 인용 검증 {sum(x['verify_ok'] for x in rows)}/{n} · 꼭 들어갈 말 {sum(x['must_say_ok'] for x in rows)}/{n} · 버전 {sum(x['version_ok'] for x in rows)}/{n} · 전체 통과 {sum(x['pass'] for x in rows)}/{n}")
print(f"모델을 부르지 않은 질문(검색 실패): {', '.join(x['id'] for x in rows if x['by'] != '모델 답변') or '없음'}")

out = ROOT / "outputs_m6"
out.mkdir(exist_ok=True)
with open(out / "answer_report.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
with open(out / "answers.jsonl", "w", encoding="utf-8") as f:
    for t, r, rec, v, ctx in shown:
        f.write(json.dumps({"id": t["id"], "question": t["question"], "route": r["route"], "flags": r["flags"], "context": [c["chunk_id"] for c in ctx],
                            "answer": rec, "verify": v}, ensure_ascii=False) + "\n")
print("저장: outputs_m6/answer_report.csv · outputs_m6/answers.jsonl")

if a.show:
    for t, r, rec, v, ctx in shown:
        print(f"\n[{t['id']}] {t['question']}")
        print(f"  넘겨준 근거: {', '.join(c['chunk_id'] for c in ctx) or '없음'}")
        print(f"  답 ({rec.get('status')}): {rec.get('answer')}")
        for c in rec.get("citations", []):
            print(f"    인용 {c.get('chunk_id')}: “{c.get('quote')}”")
        if t.get("expected_answer"):
            print(f"  평가 자료의 기대 답: {t['expected_answer']}")
