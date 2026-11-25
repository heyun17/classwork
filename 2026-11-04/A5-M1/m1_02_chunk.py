"""실습 02 · 정규화와 청킹 — 정책 본문을 소제목 단위 / 글자 수(300, 500) 단위로 잘라 비교한다.
사용 예) python m1_02_chunk.py                 # 세 방식 비교
        python m1_02_chunk.py --show POL-RET-002 --mode section
        python m1_02_chunk.py --show POL-RET-002 --mode chars --size 300 --overlap 50
"""
import argparse
import re

from m1lib import chunk_by_chars, chunk_by_section, load_policies, make_chunks, load_faq

SENT_END = re.compile(r"(다\.|요\.|\.)$")


def rule_text(doc):
    return re.search(r"## 업무 규정\n(.*?)\n\n", doc["text"], re.S).group(1).strip()


def compare(pol):
    print(f"{'방식':<16}{'정책 조각 수':>8}{'평균 길이':>8}{'최소':>6}{'최대':>6}{'문장 중간에서 끊김':>12}{'업무 규정이 한 조각에':>14}")
    for label, fn in [("소제목(##) 단위", chunk_by_section), ("글자 300 / 50", lambda d: chunk_by_chars(d, 300, 50)),
                      ("글자 500 / 50", lambda d: chunk_by_chars(d, 500, 50))]:
        pieces = [(d, p) for d in pol for p in fn(d)]
        lens = [len(p["text"]) for _, p in pieces]
        cut = sum(1 for _, p in pieces if not SENT_END.search(p["text"]))
        intact = sum(1 for d in pol if any(" ".join(rule_text(d).split()) in " ".join(p["text"].split()) for p in fn(d)))
        print(f"{label:<16}{len(pieces):>10}{sum(lens) / len(lens):>10.0f}{min(lens):>7}{max(lens):>6}"
              f"{f'{cut}/{len(pieces)}':>14}{f'{intact}/{len(pol)}':>16}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--show")
    ap.add_argument("--mode", default="section", choices=["section", "chars"])
    ap.add_argument("--size", type=int, default=300)
    ap.add_argument("--overlap", type=int, default=50)
    a = ap.parse_args()
    pol = load_policies()
    if a.show:
        d = next(x for x in pol if x["id"] == a.show)
        pieces = chunk_by_section(d) if a.mode == "section" else chunk_by_chars(d, a.size, a.overlap)
        print(f"{d['id']} · {d['title']} · {len(d['text'])}자 → {len(pieces)}조각 ({a.mode}"
              + (f" {a.size}/{a.overlap}" if a.mode == "chars" else "") + ")\n")
        for i, p in enumerate(pieces, 1):
            print(f"--- 조각 {i} [{p['section']}] {len(p['text'])}자\n{p['text']}\n")
    else:
        compare(pol)
        all_chunks = make_chunks(load_faq() + pol, "section")
        print(f"\n검색에 쓸 전체 조각 (소제목 단위): FAQ {sum(c['kind'] == 'faq' for c in all_chunks)} + 정책 {sum(c['kind'] == 'policy' for c in all_chunks)} = {len(all_chunks)}")
