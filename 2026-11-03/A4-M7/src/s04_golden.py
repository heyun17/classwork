# ====================================================================
# Step 04 · Golden Dataset 검증 → outputs/golden_validation.csv
# 원칙: 자동으로 고치지 않고 문제 목록만 출력한다.
# ====================================================================
import csv
from collections import Counter

from config import OUT_DIR
from common import load_metadata, load_golden, read_doc

meta = {m["doc_id"]: m for m in load_metadata()}
golden = load_golden()
rows = []
for g in golden:
    missing_ids = [d for d in g["relevant_doc_ids"] if d not in meta]
    texts = " ".join(read_doc(meta[d]["source_file"]) for d in g["relevant_doc_ids"] if d in meta)
    kw_missing = [k for k in g["expected_keywords"] if k not in texts]
    meta_conflict = [f"{d}.{k}" for d in g["relevant_doc_ids"] if d in meta
                     for k, v in g["required_metadata"].items()
                     if str(meta[d][k]) != str(v) and meta[d][k] != "전체"]
    rows.append({"query_id": g["query_id"], "query_type": g["query_type"], "difficulty": g["difficulty"],
                 "relevant_count": len(g["relevant_doc_ids"]), "missing_doc_ids": ",".join(missing_ids),
                 "keywords_not_in_docs": ",".join(kw_missing), "metadata_conflict": ",".join(meta_conflict)})
with open(OUT_DIR / "golden_validation.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

print("질문 수:", len(golden))
print("query_type:", dict(Counter(g["query_type"] for g in golden)))
print("difficulty:", dict(Counter(g["difficulty"] for g in golden)))
print("정답 문서 수 분포:", dict(Counter(len(g["relevant_doc_ids"]) for g in golden)))
for r in rows:
    if r["missing_doc_ids"] or r["keywords_not_in_docs"] or r["metadata_conflict"]:
        print("검토 필요:", r)
