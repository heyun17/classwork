"""M2 시작 · 지금 가진 연결로 어디까지 되나 (API 호출 없음)
사용 예) python m2_00_why.py                 # 연결 표
        python m2_00_why.py --concept 배송지연  # 한 개념이 나오는 문장 모두 보기
"""
import argparse
import re

from m1lib import find_links, load_faq, load_policies, normalize

ap = argparse.ArgumentParser()
ap.add_argument("--concept")
a = ap.parse_args()
P = load_policies()
F = load_faq()

# 같은 개념의 여러 표기 (원문에서 직접 찾은 것)
CONCEPTS = {
    "배송지연": ["배송지연", "배송 지연"],
    "판매자귀책": ["판매자 귀책", "판매자귀책", "판매자 책임"],
    "품질훼손": ["품질 훼손", "품질훼손", "변질"],
    "단순변심": ["단순 변심", "단순변심"],
    "추가배송비": ["추가배송비"],
    "제작착수": ["제작 착수", "제작착수", "제작이 시작", "제작 시작"],
    "환불소요기간": ["영업일"],
}


def sentences(text):
    for line in normalize(text).splitlines():
        if line.startswith("#"):
            continue
        for s in re.split(r"(?<=[.다])\s+", line.lstrip("-0123456789. ")):
            if s.strip():
                yield s.strip()


if a.concept:
    words = CONCEPTS.get(a.concept, [a.concept])
    print(f"'{a.concept}' 표기 {words}가 나오는 문장\n")
    for p in P:
        hits = [s for s in sentences(p["text"]) if any(w in s for w in words)]
        if hits:
            print(f"[{p['id']}] {p['title']}  ({len(hits)}문장)")
            for s in hits:
                print(f"   - {s}")
    raise SystemExit

print("[1] 문서끼리의 연결 (FAQ의 related_policy_ids 열 + 예외 본문의 '적용 정책:' 줄)\n")
inn = {p["id"]: 0 for p in P}
for f in F:
    for l in f["links"]:
        inn[l] = inn.get(l, 0) + 1
out = {p["id"]: find_links(p["text"]) for p in P}
print(f"{'정책':<12}{'FAQ가 가리킴':>10}  {'이 문서를 가리키는 정책':<26}{'이 문서가 가리키는 정책'}")
for p in P:
    pin = [q for q, v in out.items() if p["id"] in v]
    print(f"{p['id']:<12}{inn[p['id']]:>10}  {', '.join(pin) or '-':<26}{', '.join(out[p['id']]) or '-'}")
pol = [p for p in P if p["id"].startswith("POL")]
print(f"\n표준 정책 {len(pol)}개 중 다른 정책을 가리키는 문서: {sum(1 for p in pol if out[p['id']])}개")

print("\n[2] 문장 속 개념이 나오는 문서 (표기가 달라도 같은 개념으로 묶음)\n")
for c, words in CONCEPTS.items():
    docs = {}
    for p in P:
        used = [w for w in words if w in normalize(p["text"])]
        if used:
            docs[p["id"]] = used
    forms = sorted({w for v in docs.values() for w in v})
    print(f"{c:<8} 문서 {len(docs):>2}개  표기 {forms}")
    print(f"         {', '.join(docs)}")
