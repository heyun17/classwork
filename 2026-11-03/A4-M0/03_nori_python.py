# ====================================================================
# A4-M0 · Python으로 Nori 쓰기 (교안 18~19탭)
#   1) 로그인 연결 + Nori 플러그인 확인
#   2) 같은 문장을 standard / nori_tokenizer / nori 로 분석 — 토큰 글자만
#   3) 일반 명사(NNG)만 뽑기 — explain의 leftPOS로 거르기
#   4) Nori 인덱스(reviews_nori_py): 있으면 지우고 → 만들고 → 10건 넣기
#   5) 문서별 토큰 목록 (standard vs nori) + '배송' 토큰이 있는 후기
#   6) 같은 검색어를 comment(nori) / comment.std(standard)로 검색해 건수 비교
# 실행: python 03_nori_python.py   (.env 에 OPENSEARCH_PASSWORD)
# ====================================================================
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from opensearchpy import OpenSearch, helpers

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
INDEX = "reviews_nori_py"          # Dev Tools 실습(reviews_nori)과 겹치지 않게

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_auth=("admin", os.getenv("OPENSEARCH_PASSWORD")),   # 로그인 방식 (A4-M1 13탭)
    use_ssl=True, verify_certs=False, ssl_show_warn=False,
)


# ---------------------------------------------------------------- 1) 연결과 플러그인
def check():
    info = client.info()
    plugins = {p["component"] for p in client.cat.plugins(format="json")}
    print("OpenSearch", info["version"]["number"], "| analysis-nori:", "analysis-nori" in plugins)
    if "analysis-nori" not in plugins:
        raise SystemExit("Nori가 없습니다 → 교안 07탭: opensearch-plugin install analysis-nori 후 재시작")


# ---------------------------------------------------------------- 2) 분석 — 토큰 글자만
def analyze(text, analyzer=None, tokenizer=None, index=None, field=None):
    """Dev Tools의 POST _analyze 와 같은 일. 토큰 글자 리스트만 돌려준다."""
    body = {"text": text}
    if analyzer: body["analyzer"] = analyzer
    if tokenizer: body["tokenizer"] = tokenizer
    if field: body["field"] = field
    res = client.indices.analyze(body=body, index=index)
    return [t["token"] for t in res["tokens"]]


def nori_tokens(text):
    """RAG 코드에서 쓸 한국어 토크나이저 (교안 20탭)."""
    return analyze(text, analyzer="nori")


# ---------------------------------------------------------------- 3) 품사로 거르기
def tokens_with_pos(text, decompound_mode="discard"):
    """토큰마다 (글자, posType, leftPOS) — 품사 이름을 몰라도 버전과 상관없이 동작"""
    res = client.indices.analyze(body={
        "tokenizer": {"type": "nori_tokenizer", "decompound_mode": decompound_mode},
        "text": text, "explain": True, "attributes": ["posType", "leftPOS", "rightPOS"],
    })
    return [(t["token"], t.get("posType"), t.get("leftPOS", "")) for t in res["detail"]["tokenizer"]["tokens"]]


def nouns(text, tags=("NNG",)):
    """leftPOS가 tags로 시작하는 토큰만. 고유명사도 원하면 tags=("NNG", "NNP")"""
    return [tok for tok, _, pos in tokens_with_pos(text) if pos.startswith(tags)]


# ---------------------------------------------------------------- 4) Nori 인덱스
INDEX_BODY = {
    "settings": {
        "number_of_shards": 1, "number_of_replicas": 0,
        "analysis": {
            "tokenizer": {"ko_tokenizer": {"type": "nori_tokenizer", "decompound_mode": "mixed",
                                           "user_dictionary_rules": ["가성비"]}},
            "analyzer": {"ko": {"type": "custom", "tokenizer": "ko_tokenizer",
                                "filter": ["nori_part_of_speech", "nori_readingform", "lowercase"]}},
        },
    },
    "mappings": {"properties": {
        "review_id": {"type": "keyword"}, "order_id": {"type": "keyword"},
        "product": {"type": "keyword"}, "region": {"type": "keyword"}, "rating": {"type": "integer"},
        "comment": {"type": "text", "analyzer": "ko",
                    "fields": {"std": {"type": "text", "analyzer": "standard"}}},
    }},
}


def build_index():
    if client.indices.exists(index=INDEX):                 # 있으면 지우고 (교안 12탭)
        client.indices.delete(index=INDEX)
        print(f"기존 {INDEX} 삭제")
    client.indices.create(index=INDEX, body=INDEX_BODY)
    reviews = json.loads((HERE / "reviews.json").read_text(encoding="utf-8"))
    ok, _ = helpers.bulk(client, [{"_index": INDEX, "_id": r["review_id"], "_source": r} for r in reviews],
                         refresh=True)
    print(f"{INDEX}: {ok}건 저장 | _count = {client.count(index=INDEX)['count']}")


# ---------------------------------------------------------------- 5) 문서별 토큰 목록
def token_table(index=INDEX):
    hits = client.search(index=index, body={"size": 100, "sort": [{"review_id": "asc"}],
                                            "_source": ["review_id", "comment"]})["hits"]["hits"]
    rows = []
    for h in hits:
        rid, text = h["_source"]["review_id"], h["_source"]["comment"]
        std = analyze(text, index=index, field="comment.std")
        ko = analyze(text, index=index, field="comment")
        rows.append((rid, text, std, ko))
        print(f"{rid} {text}")
        print(f"     standard : {' | '.join(std)}")
        print(f"     nori(ko) : {' | '.join(ko)}")
    for name, i in [("comment.std", 2), ("comment", 3)]:
        found = [r[0] for r in rows if "배송" in r[i]]
        print(f"'배송' 토큰 [{name}] {len(found)}건 {found}")
    return rows


# ---------------------------------------------------------------- 6) 검색 비교
def compare(query, index=INDEX):
    out = {}
    for field in ["comment.std", "comment"]:
        res = client.search(index=index, body={"size": 10, "_source": ["review_id"],
                                               "query": {"match": {field: query}}})
        out[field] = [h["_source"]["review_id"] for h in res["hits"]["hits"]]
    return out


if __name__ == "__main__":
    check()

    s = "노트북 성능은 좋은데 배송이 조금 늦었어요"
    print("\n[2] 분석 비교 —", s)
    print("  standard       :", analyze(s, analyzer="standard"))
    print("  nori_tokenizer :", analyze(s, tokenizer="nori_tokenizer"))
    print("  nori 분석기     :", analyze(s, analyzer="nori"))

    print("\n[3] 품사 보기")
    for tok, ptype, pos in tokens_with_pos(s):
        print(f"  {tok:6} {ptype:9} {pos}")
    print("  NNG만:", nouns(s))

    print("\n[4] 인덱스")
    build_index()

    print("\n[5] 문서별 토큰")
    token_table()

    print("\n[6] 검색 비교  standard(comment.std) vs nori(comment)")
    for q in ["배송", "배송이 늦어요", "빠른 배송", "노트북 배터리"]:
        r = compare(q)
        print(f"  {q:10} standard {len(r['comment.std']):2}건 {r['comment.std']}")
        print(f"  {'':10} nori     {len(r['comment']):2}건 {r['comment']}")

    print("\n[RAG용] nori_tokens('MFP-GWANGJU-26은 어떤 고객을 위한 코드인가?') →",
          nori_tokens("MFP-GWANGJU-26은 어떤 고객을 위한 코드인가?"))
