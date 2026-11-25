# ====================================================================
# A4-M0 · 집계용 토큰 필드 만들기 + 단어 빈도 (교안 17·19탭)
#   text 필드(comment)는 차트로 묶을 수 없다 → Nori 토큰을 keyword 배열 필드(comment_terms)에 따로 저장
#   그러면 fielddata 없이 terms 집계·Tag Cloud가 된다.
#
#   1) comment_terms (keyword) 필드를 매핑에 추가
#   2) 문서마다 comment를 ko 분석기로 잘라 comment_terms에 저장 (조사 제거된 토큰)
#   3) Dev Tools와 같은 terms 집계로 단어 빈도 Top 15
#   4) 같은 결과를 Python Counter로 계산해 비교
# 실행: python 04_term_field.py               (기본: reviews_nori — Dev Tools에서 만든 인덱스)
#       python 04_term_field.py reviews_nori_py
# ====================================================================
import os
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from opensearchpy import OpenSearch, helpers

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
INDEX = sys.argv[1] if len(sys.argv) > 1 else "reviews_nori"
ONE_CHAR_OK = False        # True면 '북', '좋' 같은 한 글자 토큰도 남김

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_auth=("admin", os.getenv("OPENSEARCH_PASSWORD")),
    use_ssl=True, verify_certs=False, ssl_show_warn=False,
)


def ko_tokens(text):
    res = client.indices.analyze(index=INDEX, body={"field": "comment", "text": text})
    toks = [t["token"] for t in res["tokens"]]
    return toks if ONE_CHAR_OK else [t for t in toks if len(t) > 1]


if __name__ == "__main__":
    if not client.indices.exists(index=INDEX):
        raise SystemExit(f"{INDEX} 인덱스가 없습니다 → 교안 12탭(Dev Tools) 또는 03_nori_python.py 먼저")

    # 1) 매핑에 keyword 배열 필드 추가 — 기존 필드는 그대로, 새 필드만 추가는 가능
    client.indices.put_mapping(index=INDEX, body={"properties": {"comment_terms": {"type": "keyword"}}})

    # 2) 문서마다 토큰을 계산해 부분 업데이트
    hits = client.search(index=INDEX, body={"size": 1000, "_source": ["review_id", "comment"]})["hits"]["hits"]
    actions, all_tokens = [], []
    for h in hits:
        toks = ko_tokens(h["_source"]["comment"])
        all_tokens += toks
        actions.append({"_op_type": "update", "_index": INDEX, "_id": h["_id"],
                        "doc": {"comment_terms": sorted(set(toks))}})   # 문서마다 중복 없이
    ok, _ = helpers.bulk(client, actions, refresh=True)
    print(f"{INDEX}: {ok}건에 comment_terms 저장")

    # 3) terms 집계 — '그 단어가 들어 있는 후기 수'
    res = client.search(index=INDEX, body={"size": 0, "aggs": {
        "단어": {"terms": {"field": "comment_terms", "size": 15}}}})
    print("\n[집계] 단어가 들어 있는 후기 수 (Top 15)")
    for b in res["aggregations"]["단어"]["buckets"]:
        print(f"  {b['key']:8} {b['doc_count']}")

    # 4) Python Counter — '전체 등장 횟수' (한 후기에 두 번 나오면 2)
    print("\n[Counter] 전체 등장 횟수 (Top 15)")
    for w, c in Counter(all_tokens).most_common(15):
        print(f"  {w:8} {c}")
    print("\n→ Dashboards: Index patterns에서 필드 새로 고침 → Tag Cloud · Terms · comment_terms")
