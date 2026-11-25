# ====================================================================
# Step 01 · 문서 구조 확인 → outputs/document_inventory.csv, document_tree.txt
# 실행: python src/s01_document_scan.py
# ====================================================================
import csv
import re
from collections import Counter

from config import DOCS_DIR, OUT_DIR, BASE_DIR

rows, tree = [], []
files = sorted(DOCS_DIR.rglob("*.md"))
for p in files:
    text = p.read_text(encoding="utf-8")
    h1 = re.findall(r"^# (.+)$", text, flags=re.M)
    h2 = re.findall(r"^## (.+)$", text, flags=re.M)
    h3 = re.findall(r"^### (.+)$", text, flags=re.M)
    rel = p.relative_to(BASE_DIR).as_posix()
    rows.append({"source_file": rel, "folder": p.parent.name, "file_name": p.name,
                 "h1": h1[0] if h1 else "", "h2_count": len(h2), "h3_count": len(h3),
                 "sections": " | ".join(h2), "char_count": len(text)})
    tree.append(f"{p.parent.name}/{p.name}  ({len(text)}자, H2 {len(h2)}개)")

with open(OUT_DIR / "document_inventory.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
(OUT_DIR / "document_tree.txt").write_text("\n".join(tree), encoding="utf-8")

no_title = [r["source_file"] for r in rows if not r["h1"]]
empty = [r["source_file"] for r in rows if r["char_count"] == 0]
dup = [n for n, c in Counter(r["file_name"] for r in rows).items() if c > 1]
print("문서 수:", len(rows), "| 폴더:", dict(Counter(r["folder"] for r in rows)))
print("제목 없음:", no_title, "| 빈 문서:", empty, "| 중복 파일명:", dup)
print("평균 글자수:", round(sum(r["char_count"] for r in rows) / len(rows), 1))
