"""실습 03 · 메타데이터로 검색하기 — 같은 질문을 세 가지 방법으로 찾고, 설계한 답(design/answers.json)과 비교한다.
  ① 키워드만            : 조각 전체에서 키워드 점수 상위 5개
  ② 키워드 + 메타데이터  : 질문에 명시된 조건(상품 유형·지역·등급)을 통과한 조각 중 상위 5개 ('전체'는 통과)
  ③ ② + 연결 1번       : ②의 결과가 가리키는 정책(FAQ 관련 정책 열, 정책 본문의 '적용 정책')까지 포함
  ④ ② + 연결 2번       : ③에서 더해진 정책이 다시 가리키는 정책까지 포함
사용 예) python m1_03_search.py              # 요약
        python m1_03_search.py --detail Q-001
"""
import argparse
import json

from m1lib import KeywordSearch, find_links, follow_links, load_faq, load_policies, make_chunks, match

K = 5


def doc_ids(hits):
    out = []
    for h in hits:
        if h["doc_id"] not in out:
            out.append(h["doc_id"])
    return out


def run(detail=()):
    faq, pol = load_faq(), load_policies()
    by_id = {d["id"]: d for d in pol}
    chunks = make_chunks(faq + pol, "section")
    engine = KeywordSearch(chunks)
    design = json.load(open("design/answers.json", encoding="utf-8"))["questions"]
    print(f"검색 대상: 조각 {len(chunks)}개 (FAQ 80 + 정책 소제목 조각 {len(chunks) - 80}) · 상위 {K}개\n")
    print(f"{'질문':<7}{'찾아야 할 정책':>8}{'① 키워드만':>12}{'② + 메타데이터':>14}{'③ + 연결 1번':>12}{'④ + 연결 2번':>12}")
    for q in design:
        exp = q["expected"]
        h1 = engine.search(q["question"], K)
        h2 = engine.search(q["question"], K, allow=lambda c: match(c["meta"], q["conditions"]))
        r1, r2 = doc_ids(h1), doc_ids(h2)
        r3 = r2 + [x for x in follow_links(h2, by_id) if x not in r2]
        hop2 = [t for x in r3 if x in by_id and x not in r2 for t in find_links(by_id[x]["text"])]
        r4 = r3 + [x for x in dict.fromkeys(hop2) if x not in r3]
        f = lambda r: f"{sum(e in r for e in exp)}/{len(exp)}"
        print(f"{q['id']:<9}{len(exp):>8}{f(r1):>14}{f(r2):>14}{f(r3):>14}{f(r4):>13}")
        if q["id"] in detail:
            for label, hits in [("① 키워드만", h1), ("② + 메타데이터 " + json.dumps(q["conditions"], ensure_ascii=False), h2)]:
                print(f"    {label}")
                for i, h in enumerate(hits, 1):
                    mark = "정답" if h["doc_id"] in exp else ""
                    print(f"      {i}. {h['chunk_id']:<16}{mark:<4} [{h['meta']['product_type']}/{h['meta']['region']}/{h['meta']['customer_grade']}] "
                          f"{h['title'][:20]} · {h['section']}" + (f"  → 가리킴 {h['links']}" if h['links'] else ""))
            print(f"    ③ 연결 1번으로 더해진 정책: {[x for x in r3 if x not in r2]}")
            print(f"    ④ 연결 2번으로 더해진 정책: {[x for x in r4 if x not in r3]}")
            print(f"    ④까지 모은 문서 {len(r4)}개: {r4}")
            print(f"    빠진 정책: {[e for e in exp if e not in r4] or '없음'}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", nargs="*", default=[])
    run(ap.parse_args().detail)
