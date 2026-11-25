"""실습 07 · 같은 개체 합치기와 관계 이름 정리
1) triples_free.json에서 같은 것을 다르게 부른 이름과 관계 이름을 센다.
2) design/m2_alias.json(별칭표)이 있으면 적용해서 전후를 비교한다. 없으면 초안을 만들어 준다.
3) triples_schema.json이 있으면 자유 추출과 스키마 추출을 나란히 비교한다.
사용 예) python m2_07_normalize.py
"""
import json
import re
from collections import Counter, defaultdict

from m2lib import OUT, ROOT

schema = json.loads((ROOT / "design" / "m2_schema.json").read_text(encoding="utf-8"))
SCHEMA_NAMES = {n: t for t, v in schema["entity_types"].items() for n in v.get("names", [])}
SCHEMA_PREDS = {p["name"] for p in schema["predicates"]}
DOC_ID = re.compile(r"^(POL|EXC)-[A-Z]*-?\d+$")


def key(name):
    """띄어쓰기·가운뎃점·'상품' 꼬리를 떼어 낸 비교용 열쇠"""
    k = re.sub(r"[\s·_\-]", "", name)
    return k[:-2] if k.endswith("상품") and len(k) > 3 else k


def load(mode):
    p = OUT / f"triples_{mode}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def stats(triples):
    names = Counter([t["subject"] for t in triples] + [t["object"] for t in triples])
    return names, Counter(t["predicate"] for t in triples)


def apply(triples, alias):
    ent, pred = alias.get("entities", {}), alias.get("predicates", {})
    return [dict(t, subject=ent.get(t["subject"], t["subject"]), object=ent.get(t["object"], t["object"]),
                 predicate=pred.get(t["predicate"], t["predicate"])) for t in triples]


free = load("free")
if not free:
    raise SystemExit("outputs_m2/triples_free.json이 없습니다. 먼저 python m2_06_extract_all.py --mode free")
T = free["triples"]
names, preds = stats(T)

print(f"[1] 자유 추출 결과 · triple {len(T)}개 · 개체 이름 {len(names)}개 · 관계 이름 {len(preds)}개\n")
groups = defaultdict(list)
for n in names:
    groups[key(n)].append(n)
variants = {k: sorted(v, key=lambda x: -names[x]) for k, v in groups.items() if len(v) > 1}
print(f"같은 것을 다르게 부른 이름 {len(variants)}묶음")
for k, v in sorted(variants.items(), key=lambda kv: -sum(names[x] for x in kv[1]))[:15]:
    print("  " + " / ".join(f"{x}({names[x]})" for x in v))

print(f"\n관계 이름 {len(preds)}개 중 한 번만 나온 것 {sum(1 for c in preds.values() if c == 1)}개")
print("  " + ", ".join(f"{p}({c})" for p, c in preds.most_common(25)))

# ---------------------------------------------------------------- 별칭표
alias_path = ROOT / "design" / "m2_alias.json"
if not alias_path.exists():
    draft = {"entities": {}, "predicates": {}}
    sch0 = load("schema")
    if sch0:  # 스키마 추출 결과의 이름도 함께 본다
        for t in sch0["triples"]:
            for n in (t["subject"], t["object"]):
                names.setdefault(n, 0)
                if n not in groups[key(n)]:
                    groups[key(n)].append(n)
        variants = {k: v for k, v in groups.items() if len(v) > 1}
    for k, v in variants.items():
        target = next((s for s in SCHEMA_NAMES if key(s) == k), min(v, key=lambda x: (" " in x, -names[x])))
        for x in v:
            if x != target:
                draft["entities"][x] = target
    for n in names:
        if n not in draft["entities"] and n not in SCHEMA_NAMES:
            hit = next((s for s in SCHEMA_NAMES if key(s) == key(n)), None)
            if hit:
                draft["entities"][n] = hit
    draft["predicates"] = {p: "" for p, _ in preds.most_common()}
    out = ROOT / "design" / "m2_alias_draft.json"
    out.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[2] 별칭표가 없어 초안을 만들었습니다: {out.relative_to(ROOT)}")
    print("    개체 이름 합치기는 자동으로 채웠고, 관계 이름은 빈칸입니다.")
    print("    빈칸을 스키마 관계 이름(" + ", ".join(sorted(SCHEMA_PREDS)) + ")으로 채우고")
    print("    design/m2_alias.json으로 저장한 뒤 다시 실행하세요.")
else:
    alias = json.loads(alias_path.read_text(encoding="utf-8"))
    alias["predicates"] = {k: v for k, v in alias.get("predicates", {}).items() if v}
    N = apply(T, alias)
    n2, p2 = stats(N)
    print(f"\n[2] 별칭표 적용 · 개체 이름 {len(names)} → {len(n2)}개 · 관계 이름 {len(preds)} → {len(p2)}개")
    in_vocab = sum(1 for t in N if t["predicate"] in SCHEMA_PREDS)
    print(f"    스키마 관계 이름으로 바뀐 triple {in_vocab}/{len(N)}개")
    (OUT / "triples_free_normalized.json").write_text(json.dumps({"mode": "free+alias", "triples": N}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("    저장: outputs_m2/triples_free_normalized.json")

# ---------------------------------------------------------------- 자유 vs 스키마
sch = load("schema")
if sch:
    sc = json.loads((ROOT / (sch.get("schema") or "design/m2_schema.json")).read_text(encoding="utf-8"))
    SCHEMA_NAMES = {n: t for t, v in sc["entity_types"].items() for n in v.get("names", [])}
    SCHEMA_PREDS = {p["name"] for p in sc["predicates"]}
    S = sch["triples"]
    sn, sp = stats(S)
    out_name = [n for n in sn if n not in SCHEMA_NAMES and not DOC_ID.match(n)]
    out_pred = [p for p in sp if p not in SCHEMA_PREDS]
    print(f"\n[3] 자유 추출 vs 스키마 추출 (스키마 {sc['version']})")
    print(f"    {'':<22}{'자유':>8}{'스키마':>8}")
    print(f"    {'triple 수':<22}{len(T):>8}{len(S):>8}")
    print(f"    {'개체 이름 수':<22}{len(names):>8}{len(sn):>8}")
    print(f"    {'관계 이름 수':<22}{len(preds):>8}{len(sp):>8}")
    print(f"    스키마에 없는 관계 이름: {out_pred or '없음'}")
    print(f"    이름 목록 밖의 개체(확인항목 포함) {len(out_name)}개: {', '.join(sorted(out_name)[:20])}")
else:
    print("\n[3] triples_schema.json이 없어 비교를 건너뜁니다 (python m2_06_extract_all.py --mode schema)")
