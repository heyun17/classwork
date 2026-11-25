"""실습 08 · 온톨로지 결과를 JSON으로 저장하기 (근거 검증 포함)
- 입력: outputs_m2/triples_schema.json (+ design/m2_alias.json이 있으면 이름 정리)
- 검사: 관계 이름이 스키마에 있는가 · 개체 이름이 목록에 있는가 · 근거 문장이 원문에 그대로 있는가
- 출력: outputs_m2/ontology.json (nodes, edges, properties, rejected)
- 비교: reference/ontology_gold_triples.csv와 문서별로 나란히 본다
사용 예) python m2_08_save.py
"""
import csv
import json
import re
from collections import Counter

from m2lib import OUT, ROOT, load_policies, normalize

import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--triples", default="outputs_m2/triples_schema.json")
a = ap.parse_args()
src = json.loads((ROOT / a.triples).read_text(encoding="utf-8"))
schema = json.loads((ROOT / (src.get("schema") or "design/m2_schema_v0.1.json")).read_text(encoding="utf-8"))
TYPE_OF = {n: t for t, v in schema["entity_types"].items() for n in v.get("names", [])}
PRED = {p["name"]: p for p in schema["predicates"]}
DOC_ID = re.compile(r"^(POL|EXC)-[A-Z]*-?\d+$")
alias_path = ROOT / "design" / "m2_alias.json"
alias = json.loads(alias_path.read_text(encoding="utf-8")) if alias_path.exists() else {}
EA = alias.get("entities", {})

docs = {d["id"]: d for d in load_policies()}


def squash(s):
    return re.sub(r"\s+", "", normalize(s or ""))


def section_of(doc, quote):
    """근거 문장이 들어 있는 '## 소제목'을 찾는다. 원문에 없으면 None"""
    q = squash(quote)
    if not q:
        return None
    sec = "(머리)"
    for line in normalize(doc["text"]).splitlines():
        if line.startswith("## "):
            sec = line[3:].strip()
        elif q in squash(line):
            return sec
    return None


def type_of(name, declared):
    if DOC_ID.match(name):
        return "정책"
    if name in TYPE_OF:
        return TYPE_OF[name]
    return "확인항목" if declared == "확인항목" else None


edges, rejected, seen = [], [], set()
for t in src["triples"]:
    s, p, o = EA.get(t["subject"], t["subject"]), t["predicate"], EA.get(t["object"], t["object"])
    st, ot = type_of(s, t.get("subject_type")), type_of(o, t.get("object_type"))
    sec = section_of(docs[t["doc_id"]], t.get("evidence", ""))
    reason = None
    if p not in PRED:
        reason = "스키마에 없는 관계"
    elif st is None or ot is None:
        reason = "목록에 없는 개체 이름"
    elif st not in PRED[p]["subject"].split("|") or ot not in PRED[p]["object"].split("|"):
        reason = f"관계 방향 불일치 ({st} → {ot})"
    elif sec is None:
        reason = "근거 문장이 원문에 없음"
    row = {"subject": s, "predicate": p, "object": o, "doc_id": t["doc_id"], "section": sec, "evidence": t.get("evidence", "")}
    if reason:
        rejected.append(dict(row, reason=reason))
    elif (s, p, o) not in seen:
        seen.add((s, p, o))
        edges.append(dict(row, subject_type=st, object_type=ot))

nodes = {}
for e in edges:
    nodes[e["subject"]] = e["subject_type"]
    nodes[e["object"]] = e["object_type"]
props = []
for p in src.get("properties", []):
    sec = section_of(docs[p["doc_id"]], p.get("evidence", ""))
    props.append(dict(p, entity=EA.get(p.get("entity"), p.get("entity")), section=sec, verified=sec is not None))

onto = {"schema_version": schema["version"], "source": a.triples,
        "nodes": [{"id": n, "type": t} for n, t in sorted(nodes.items(), key=lambda x: (x[1], x[0]))],
        "edges": edges, "properties": props, "rejected": rejected}
text = json.dumps(onto, ensure_ascii=False, indent=2)
(OUT / "ontology.json").write_text(text, encoding="utf-8")
(OUT / f"ontology_v{schema['version']}.json").write_text(text, encoding="utf-8")

print(f"입력 triple {len(src['triples'])}개 → 저장 {len(edges)}개 · 버림 {len(rejected)}개 · 중복 {len(src['triples']) - len(edges) - len(rejected)}개")
for r, c in Counter(r["reason"] for r in rejected).most_common():
    print(f"  버린 이유: {r} {c}개")
print(f"노드 {len(nodes)}개 · 종류별: " + ", ".join(f"{t} {c}" for t, c in Counter(nodes.values()).most_common()))
print(f"관계별: " + ", ".join(f"{p} {c}" for p, c in Counter(e['predicate'] for e in edges).most_common()))
print(f"속성 {len(props)}개 · 근거 확인 {sum(p['verified'] for p in props)}개")
print(f"스키마 {schema['version']} · 저장: outputs_m2/ontology.json (+ ontology_v{schema['version']}.json)")

# ---------------------------------------------------------------- 정답 예시와 비교
gold_path = ROOT / "reference" / "ontology_gold_triples.csv"
if gold_path.exists():
    gold = list(csv.DictReader(open(gold_path, encoding="utf-8-sig")))
    gp = Counter(g["predicate"] for g in gold)
    print(f"\n[정답 예시 비교] reference/ontology_gold_triples.csv · triple {len(gold)}개 · 관계 이름 {len(gp)}개")
    mine = {(e["doc_id"]) for e in edges}
    gdocs = Counter(g["evidence_doc_id"] for g in gold)
    print(f"  정답 예시가 근거로 쓴 문서 {len(gdocs)}개 중 우리 결과에도 triple이 있는 문서 {sum(1 for d in gdocs if d in mine)}개")
    mynames = {squash(n) for n in nodes}
    gnames = {squash(x) for g in gold for x in (g["subject"], g["object"])}
    both = sorted(mynames & gnames)
    print(f"  개체 이름이 똑같이 겹치는 것 {len(both)}개: {', '.join(both[:20])}")
