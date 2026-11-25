"""실습 04 · 필수 조건과 선택 조건 — 조건을 어떻게 거느냐에 따라 결과가 어떻게 바뀌는지 비교한다.
  A 조건 없음
  B 업무 영역(category)을 필수로        : 질문의 업무 영역과 category가 같은 조각만
  C 명시 조건을 필수로, '전체'는 제외   : 상품 유형·지역·등급이 질문과 정확히 같은 조각만
  D 명시 조건을 필수로, '전체'는 통과   : 질문과 같거나 '전체'인 조각
  E D + 업무 영역은 선택(점수 1.5배)    : 업무 영역이 같으면 점수만 올리고, 다르다고 거르지는 않음
  F E + 연결 2번                        : E의 결과가 가리키는 정책까지 (실습 03의 ④)
보는 것: 정답(설계한 정책) 몇 개 · 조건과 어긋난 조각 몇 개 · 모인 문서 몇 개
"""
import json

from m1lib import KeywordSearch, find_links, follow_links, load_faq, load_policies, make_chunks, match

K = 5
faq, pol = load_faq(), load_policies()
by_id = {d["id"]: d for d in pol}
chunks = make_chunks(faq + pol, "section")
engine = KeywordSearch(chunks)
design = json.load(open("design/answers.json", encoding="utf-8"))["questions"]


def ids(hits):
    return list(dict.fromkeys(h["doc_id"] for h in hits))


def conflicts(hits, cond):
    """질문 조건과 맞지 않는 조각 수 ('전체'는 맞는 것으로 본다)."""
    return sum(1 for h in hits if not match(h["meta"], cond))


strategies = {
    "A 조건 없음": lambda q: None,
    "B 업무 영역 필수": lambda q: (lambda c: c["meta"]["category"] in q["domains"]),
    "C 명시 조건 필수 · 전체 제외": lambda q: (lambda c: match(c["meta"], q["conditions"], wildcard=False)),
    "D 명시 조건 필수 · 전체 통과": lambda q: (lambda c: match(c["meta"], q["conditions"])),
    "E D + 업무 영역 선택": lambda q: (lambda c: match(c["meta"], q["conditions"])),
}
BOOST = {"E D + 업무 영역 선택": lambda q: (lambda c: 1.5 if c["meta"]["category"] in q["domains"] else 1.0)}
print(f"{'질문':<7}" + "".join(f"{k:>22}" for k in list(strategies) + ["F E + 연결 2번"]))
total = {k: [0, 0, 0] for k in list(strategies) + ["F"]}
for q in design:
    exp, row = q["expected"], []
    for name, mk in strategies.items():
        hits = engine.search(q["question"], K, allow=mk(q), boost=BOOST[name](q) if name in BOOST else None)
        got = ids(hits)
        hit, bad = sum(e in got for e in exp), conflicts(hits, q["conditions"])
        row.append(f"정답 {hit}/{len(exp)} · 어긋남 {bad}")
        total[name][0] += hit; total[name][1] += bad; total[name][2] += len(got)
        if name.startswith("E"):
            r3 = got + [x for x in follow_links(hits, by_id) if x not in got]
            hop2 = [t for x in r3 if x in by_id and x not in got for t in find_links(by_id[x]["text"])]
            r4 = r3 + [x for x in dict.fromkeys(hop2) if x not in r3]
            e_hit = sum(e in r4 for e in exp)
            total["F"][0] += e_hit; total["F"][2] += len(r4)
            e_txt = f"정답 {e_hit}/{len(exp)} · 문서 {len(r4)}"
    print(f"{q['id']:<9}" + "".join(f"{x:>24}" for x in row) + f"{e_txt:>24}")
n_exp = sum(len(q["expected"]) for q in design)
print("\n합계 (7개 질문)")
for k, (h, b, n) in total.items():
    label = k if k != "F" else "F E + 연결 2번"
    print(f"  {label:<24} 정답 {h}/{n_exp}" + (f" · 어긋난 조각 {b}" if k != "F" else "") + f" · 모인 문서 {n}")
