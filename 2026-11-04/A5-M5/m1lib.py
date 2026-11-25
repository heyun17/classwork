"""A5-M1 실습 공통 코드 — dataset/ 폴더를 읽고, 자르고, 찾는다.

자료
  dataset/faq.csv       고객 질문·답변 (한 행 = 문서 하나), 메타데이터 열 포함
  dataset/policies.csv  정책 목록 (메타데이터 + 본문 파일 링크)
  dataset/md/*.md       정책 본문 (마크다운)
문서 하나는 같은 모양의 dict로 다룬다.
  {"id", "kind", "title", "text", "meta": {...}, "links": [...]}
"""
import csv
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent / "dataset"
META_FIELDS = ["category", "product_type", "region", "customer_grade", "order_status"]
WILDCARD = "전체"
ID_PATTERN = re.compile(r"(?:POL|EXC)-[A-Z]*-?\d{3}")


# ------------------------------------------------------------------ 실습 01 · 로딩
def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:  # BOM이 있는 CSV
        return list(csv.DictReader(f))


def load_faq():
    docs = []
    for r in read_csv(DATA / "faq.csv"):
        docs.append({"id": r["doc_id"], "kind": "faq", "title": r["question"],
                     "text": f"질문: {r['question']}\n답변: {r['answer']}",
                     "meta": {k: r[k] for k in META_FIELDS},
                     "links": [x for x in r["related_policy_ids"].split("|") if x]})
    return docs


def load_policies():
    docs = []
    for r in read_csv(DATA / "policies.csv"):
        text = (DATA / r["file"]).read_text(encoding="utf-8")  # 목록의 링크를 따라 본문을 읽는다
        docs.append({"id": r["doc_id"], "kind": "policy", "title": r["title"], "text": text,
                     "meta": dict({k: r[k] for k in META_FIELDS}, doc_type=r["doc_type"]),
                     "links": []})
    return docs


def load_all():
    return load_faq() + load_policies()


# ------------------------------------------------------------------ 실습 02 · 정규화와 청킹
def normalize(text):
    """유니코드 NFC + 줄 끝 공백 제거 + 빈 줄 여러 개를 하나로. 줄바꿈(마크다운 구조)은 남긴다."""
    text = unicodedata.normalize("NFC", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def flatten(text):
    """글자 수로 자를 때 쓰는 한 줄 텍스트: 모든 공백을 한 칸으로."""
    return re.sub(r"\s+", " ", normalize(text)).strip()


def chunk_by_section(doc):
    """마크다운 '## 소제목' 단위로 자른다. 각 조각 앞에 '문서 제목 > 소제목'을 붙인다."""
    text = normalize(doc["text"])
    parts = re.split(r"\n(?=## )", text)
    title = parts[0].lstrip("# ").splitlines()[0]
    chunks = []
    for part in parts[1:]:
        head, _, body = part.partition("\n")
        section = head.lstrip("# ").strip()
        chunks.append({"section": section, "text": f"{title} > {section}\n{body.strip()}"})
    return chunks


def chunk_by_chars(doc, size=300, overlap=50):
    """글자 수 창으로 자른다. 다음 창은 (size - overlap) 뒤에서 시작한다."""
    text = flatten(doc["text"])
    step, start, chunks = size - overlap, 0, []
    while start < len(text):
        chunks.append({"section": f"{start}~{min(start + size, len(text))}자", "text": text[start:start + size].strip()})
        if start + size >= len(text):
            break
        start += step
    return chunks


def make_chunks(docs, mode="section", size=300, overlap=50):
    """FAQ는 한 행이 이미 짧으므로 그대로 한 조각. 정책 본문만 자른다."""
    out = []
    for d in docs:
        if d["kind"] == "faq":
            pieces = [{"section": "FAQ", "text": normalize(d["text"])}]
        elif mode == "section":
            pieces = chunk_by_section(d)
        else:
            pieces = chunk_by_chars(d, size, overlap)
        for i, p in enumerate(pieces, 1):
            out.append({"chunk_id": f"{d['id']}#{i}", "doc_id": d["id"], "kind": d["kind"], "title": d["title"],
                        "section": p["section"], "text": p["text"], "meta": d["meta"], "links": d["links"]})
    return out


# ------------------------------------------------------------------ 실습 03 · 검색
def grams(text):
    t = flatten(text)
    return [t[i:i + 2] for i in range(len(t) - 1) if " " not in t[i:i + 2]]


class KeywordSearch:
    """질문과 겹치는 2글자 조각이 많고, 그 조각이 드물수록 점수가 높다."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.tf = [Counter(grams(c["text"])) for c in chunks]
        df = Counter(g for tf in self.tf for g in tf)
        self.idf = {g: math.log(1 + len(chunks) / n) for g, n in df.items()}

    def scores(self, query):
        q = set(grams(query))
        return [sum(min(tf[g], 3) * self.idf[g] for g in q if g in tf) / math.sqrt(sum(tf.values()) + 1) for tf in self.tf]

    def search(self, query, k=5, allow=None, boost=None):
        """allow: 조각 → True/False (필수 조건, 통과한 조각만 남김)
        boost: 조각 → 배수 (선택 조건, 점수만 올림. 거르지는 않음)"""
        sc = self.scores(query)
        if boost:
            sc = [s * boost(c) for s, c in zip(sc, self.chunks)]
        order = sorted(range(len(self.chunks)), key=lambda i: -sc[i])
        hits = [self.chunks[i] for i in order if sc[i] > 0 and (allow is None or allow(self.chunks[i]))]
        return hits[:k]


def match(meta, conditions, wildcard=True):
    """conditions: {"열": "값" 또는 ["값", ...]}. wildcard=True면 문서 값이 '전체'일 때도 통과."""
    for field, want in conditions.items():
        want = [want] if isinstance(want, str) else want
        ok = meta.get(field) in want or (wildcard and meta.get(field) == WILDCARD)
        if not ok:
            return False
    return True


def find_links(text):
    """정책 본문의 '적용 정책: ...' 줄에 적힌 문서 ID."""
    m = re.search(r"적용 정책: ([^.\n]*)", text)
    return ID_PATTERN.findall(m.group(1)) if m else []


def follow_links(hits, policies_by_id):
    """결과 조각이 가리키는 정책(FAQ의 related_policy_ids, 정책 본문의 '적용 정책')을 모은다."""
    found = []
    for h in hits:
        if h["kind"] == "faq":
            targets = h["links"]                                          # FAQ → 열에 적힌 정책
        else:
            targets = find_links(policies_by_id[h["doc_id"]]["text"])     # 정책 → 본문의 '적용 정책'

        for t in targets:
            if t not in found:
                found.append(t)
    return found
