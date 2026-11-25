# ====================================================================
# 파일 용도: 여러 Step이 함께 쓰는 함수 — 데이터 읽기, 토큰화, 메타데이터 필터, 평가 지표
# ====================================================================
import csv
import json
import math
import re

from config import METADATA_CSV, GOLDEN_JSON, OUT_DIR, BASE_DIR


def load_metadata():
    with open(METADATA_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["year"] = int(r["year"])
    return rows


def load_golden():
    return json.loads(GOLDEN_JSON.read_text(encoding="utf-8"))


def load_chunks(method):
    return json.loads((OUT_DIR / f"chunks_{method}.json").read_text(encoding="utf-8"))


def read_doc(source_file):
    return (BASE_DIR / source_file).read_text(encoding="utf-8")


# ---------- 토큰화 (BM25용) ----------
PARTICLES = ("에서", "으로", "과", "와", "은", "는", "이", "가", "을", "를", "의", "에", "로", "도")


def tokenize(text):
    """영문·숫자·하이픈 제품코드는 그대로, 한글 단어는 흔한 조사를 하나 떼어 함께 넣는다."""
    tokens = []
    for t in re.findall(r"[0-9A-Za-z가-힣/\-]+", text.lower()):
        tokens.append(t)
        if re.fullmatch(r"[가-힣]+", t) and len(t) > 2:
            for p in PARTICLES:
                if t.endswith(p):
                    tokens.append(t[: -len(p)])
                    break
    return tokens


# ---------- 질문에서 메타데이터 조건 뽑기 ----------
REGIONS = ["서울", "부산", "광주", "대전"]
YEARS = [2025, 2026]
CUSTOMERS = ["공공기관", "기업"]
PRODUCTS = ["노트북", "복합기"]


def extract_filters(question):
    """질문에 '하나만' 분명히 나오는 조건만 필터로 쓴다. 둘 이상이면 비교 질문이라 걸지 않는다."""
    f = {}
    regions = [r for r in REGIONS if r in question]
    years = [y for y in YEARS if str(y) in question]
    customers = [c for c in CUSTOMERS if c in question]
    products = [p for p in PRODUCTS if p in question]
    if len(regions) == 1:
        f["region"] = regions[0]
    if len(years) == 1:
        f["year"] = years[0]
    if len(customers) == 1:
        f["customer_type"] = customers[0]
    if len(products) == 1:
        f["product"] = products[0]
    return f


def match_filters(chunk, filters):
    """메타데이터 값이 '전체'인 문서(시장현황)는 고객·제품 조건에 걸러지지 않게 둔다."""
    for k, v in filters.items():
        cv = chunk[k]
        if cv == v:
            continue
        if cv == "전체" and k in ("customer_type", "product"):
            continue
        return False
    return True


# ---------- 청크 순위 → 문서 순위 ----------
def to_doc_ranking(ranked_chunks, k):
    """청크 순위에서 처음 나온 문서 순서대로 중복 없이 K개"""
    docs, used = [], []
    for c in ranked_chunks:
        if c["doc_id"] not in docs:
            docs.append(c["doc_id"])
            used.append(c)
        if len(docs) == k:
            break
    return docs, used


# ---------- 평가 지표 ----------
def precision_at_k(ranked, relevant, k):
    return sum(1 for d in ranked[:k] if d in relevant) / k


def recall_at_k(ranked, relevant, k):
    return sum(1 for d in ranked[:k] if d in relevant) / len(relevant)


def hit_at_k(ranked, relevant, k):
    return 1.0 if any(d in relevant for d in ranked[:k]) else 0.0


def reciprocal_rank(ranked, relevant):
    for i, d in enumerate(ranked, 1):
        if d in relevant:
            return 1 / i
    return 0.0


def ndcg_at_k(ranked, relevant, k):
    dcg = sum(1 / math.log2(i + 1) for i, d in enumerate(ranked[:k], 1) if d in relevant)
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal else 0.0
