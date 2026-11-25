"""실습 06 · 정책 문서 19개 전체에서 Triple 만들기
사용 예) python m2_06_extract_all.py --mode free     # 형식만 알려 주고 자유롭게 뽑기
        python m2_06_extract_all.py --mode schema   # design/m2_schema.json의 이름과 관계로만 뽑기
        python m2_06_extract_all.py --mode free --dry-run   # 첫 문서의 프롬프트만 보기
결과: outputs_m2/triples_<mode>.json  (문서마다 API 원본은 outputs_m2/raw/<mode>_<문서ID>.json)
"""
import argparse
import json
from collections import Counter

from m2lib import OUT, SYSTEM, ask_json, free_prompt, load_policies, schema_prompt, ROOT

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=["free", "schema"], default="free")
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--refresh", action="store_true")
ap.add_argument("--schema", default="design/m2_schema.json", help="스키마 파일 (schema 모드)")
a = ap.parse_args()

schema = json.loads((ROOT / a.schema).read_text(encoding="utf-8"))
ver = schema["version"]
# 기록 파일 이름: 자유 → free_문서, 스키마 0.1 → schema_문서, 그 뒤 버전 → schema_v0.2_문서
tag = "free" if a.mode == "free" else ("schema" if ver == "0.1" else f"schema_v{ver}")
docs = load_policies()
if a.dry_run:
    d = docs[0]
    ask_json(f"{tag}_{d['id']}", SYSTEM, free_prompt(d) if a.mode == "free" else schema_prompt(d, schema), dry_run=True)
    raise SystemExit

triples, props, ents = [], [], []
tok_in = tok_out = sec = 0
print(f"모드: {a.mode}" + (f" · 스키마 {ver}" if a.mode == "schema" else "") + f" · 문서 {len(docs)}개\n")
print(f"{'문서':<12} {'triple':>6} {'property':>8}  {'초':>5}")
for d in docs:
    prompt = free_prompt(d) if a.mode == "free" else schema_prompt(d, schema)
    rec = ask_json(f"{tag}_{d['id']}", SYSTEM, prompt, refresh=a.refresh)
    data = rec["data"]
    ts = [dict(t, doc_id=d["id"]) for t in data.get("triples", [])]
    ps = [dict(p, doc_id=d["id"]) for p in data.get("properties", [])]
    triples += ts
    props += ps
    ents += [dict(e, doc_id=d["id"]) for e in data.get("entities", [])]
    tok_in += rec["usage"]["prompt_tokens"]
    tok_out += rec["usage"]["completion_tokens"]
    sec += rec["seconds"]
    print(f"{d['id']:<12} {len(ts):>6} {len(ps):>8}  {rec['seconds']:>5}")

OUT.mkdir(exist_ok=True)
path = OUT / f"triples_{a.mode}.json"
body = json.dumps({"mode": a.mode, "schema": a.schema if a.mode == "schema" else None, "schema_version": ver if a.mode == "schema" else None,
                   "triples": triples, "properties": props, "entities": ents}, ensure_ascii=False, indent=2)
path.write_text(body, encoding="utf-8")
if a.mode == "schema":  # 버전별로도 남겨 두고 비교한다
    (OUT / f"triples_schema_v{ver}.json").write_text(body, encoding="utf-8")
preds = Counter(t["predicate"] for t in triples)
names = {t["subject"] for t in triples} | {t["object"] for t in triples}
print(f"\n합계 triple {len(triples)}개 · property {len(props)}개 · 토큰 입력 {tok_in} / 출력 {tok_out} · {sec:.0f}초")
print(f"서로 다른 관계 이름 {len(preds)}개 · 서로 다른 개체 이름 {len(names)}개")
print("많이 나온 관계 이름:", ", ".join(f"{p}({n})" for p, n in preds.most_common(12)))
print(f"저장: {path.relative_to(ROOT)}")
