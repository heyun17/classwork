# ====================================================================
# Step 02 · metadata.csv 검증 → outputs/metadata_validation.csv
# 원칙: 문서를 보고 metadata를 임의로 고치지 않는다. 검증만 한다.
# ====================================================================
import csv
from collections import Counter

from config import DOCS_DIR, OUT_DIR, BASE_DIR
from common import load_metadata

REQUIRED = ["doc_id", "year", "region", "customer_type", "product", "doc_type", "product_code", "source_file"]
meta = load_metadata()
doc_files = {p.relative_to(BASE_DIR).as_posix() for p in DOCS_DIR.rglob("*.md")}
dup_ids = {d for d, c in Counter(m["doc_id"] for m in meta).items() if c > 1}

out = []
for m in meta:
    missing = [k for k in REQUIRED if k not in m or (m[k] == "" and k != "product_code")]
    out.append({"doc_id": m["doc_id"], "source_exists": m["source_file"] in doc_files,
                "duplicate_id": m["doc_id"] in dup_ids, "missing_fields": ",".join(missing),
                "product_code_empty": m["product_code"] == ""})
with open(OUT_DIR / "metadata_validation.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)

print("metadata 행:", len(meta), "| 실제 문서:", len(doc_files), "| 1:1 대응:", len(meta) == len(doc_files))
print("파일 없음:", [o["doc_id"] for o in out if not o["source_exists"]])
print("doc_id 중복:", sorted(dup_ids), "| 필수값 누락:", [o["doc_id"] for o in out if o["missing_fields"]])
print("product_code 빈 문서(시장현황):", sum(o["product_code_empty"] for o in out))
for k in ["year", "region", "customer_type", "product", "doc_type"]:
    print(f"  {k}:", dict(Counter(m[k] for m in meta)))
