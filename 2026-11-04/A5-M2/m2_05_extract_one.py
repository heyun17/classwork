"""실습 05 · 문서 하나에서 개체·관계·속성 뽑기 (OpenAI API)
사용 예) python m2_05_extract_one.py --dry-run          # 보낼 프롬프트만 보기 (API 호출 없음)
        python m2_05_extract_one.py                    # EXC-001을 실제로 추출
        python m2_05_extract_one.py --doc POL-RET-002
"""
import argparse
import json

from m2lib import MODEL, SYSTEM, ask_json, free_prompt, policy

ap = argparse.ArgumentParser()
ap.add_argument("--doc", default="EXC-001")
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--refresh", action="store_true")
a = ap.parse_args()

doc = policy(a.doc)
rec = ask_json(f"free_{a.doc}", SYSTEM, free_prompt(doc), a.dry_run, a.refresh)
if rec:
    d = rec["data"]
    print(f"{a.doc} · 모델 {rec['model']} · {rec['seconds']}초 · 토큰 입력 {rec['usage']['prompt_tokens']} / 출력 {rec['usage']['completion_tokens']}")
    print(f"저장: outputs_m2/raw/free_{a.doc}.json\n")
    print(f"[entities] {len(d.get('entities', []))}개")
    for e in d.get("entities", []):
        print(f"  {e.get('name')}  ({e.get('type')})")
    print(f"\n[triples] {len(d.get('triples', []))}개")
    for t in d.get("triples", []):
        print(f"  ({t.get('subject')}, {t.get('predicate')}, {t.get('object')})\n      근거: {t.get('evidence', '')[:70]}")
    print(f"\n[properties] {len(d.get('properties', []))}개")
    for p in d.get("properties", []):
        print(f"  {p.get('entity')} · {p.get('name')} = {p.get('value')}")
