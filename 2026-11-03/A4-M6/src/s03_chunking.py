# ====================================================================
# Step 03 · 세 가지 청킹 → outputs/chunks_<방식>.json, chunk_stats.csv, chunk_sample.csv
# ====================================================================
import csv
import json
import re
import statistics

from config import OUT_DIR, CHUNK_METHODS, META_FIELDS
from common import load_metadata, read_doc

MIN_CHARS = 40          # 이보다 짧으면 '지나치게 짧은 청크'
MAX_CHARS = 500         # 이보다 길면 '지나치게 긴 청크'


def chunk_heading(text):
    """H2(## ) 단위로 자르고, 앞의 H1 제목을 각 청크 맨 앞에 붙인다. 너무 짧은 섹션은 다음과 합친다."""
    title = re.findall(r"^# (.+)$", text, flags=re.M)[0]
    parts = [p.strip() for p in re.split(r"\n(?=## )", text) if p.strip().startswith("## ")]
    merged, buf = [], ""
    for p in parts:
        buf = (buf + "\n\n" + p).strip() if buf else p
        if len(buf) >= MIN_CHARS:
            merged.append(buf); buf = ""
    if buf:
        if merged: merged[-1] += "\n\n" + buf
        else: merged.append(buf)
    return [f"# {title}\n{m}" for m in merged]


def chunk_fixed(text, size, overlap=0):
    step = size - overlap
    return [text[i:i + size] for i in range(0, max(len(text) - overlap, 1), step)]


SPLITTERS = {
    "heading": chunk_heading,
    "fixed_300": lambda t: chunk_fixed(t, 300),
    "fixed_500_overlap_100": lambda t: chunk_fixed(t, 500, 100),
}

meta = load_metadata()
stats, samples = [], []
for method in CHUNK_METHODS:
    chunks = []
    for m in meta:
        for i, piece in enumerate(SPLITTERS[method](read_doc(m["source_file"]))):
            c = {"chunk_id": f'{m["doc_id"]}__{method}__{i:02d}', "doc_id": m["doc_id"],
                 "chunk_method": method, "chunk_order": i, "content": piece, "char_count": len(piece),
                 "source_file": m["source_file"], **{k: m[k] for k in META_FIELDS}}
            chunks.append(c)
    (OUT_DIR / f"chunks_{method}.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")

    sizes = [c["char_count"] for c in chunks]
    contents = [re.sub(r"\s+", " ", c["content"]) for c in chunks]
    dup = len(contents) - len(set(contents))
    inherit_ok = sum(all(c[k] == m[k] for k in META_FIELDS)
                     for c in chunks for m in meta if m["doc_id"] == c["doc_id"]) / len(chunks)
    stats.append({"chunk_method": method, "chunks": len(chunks), "avg_chars": round(statistics.mean(sizes), 1),
                  "min_chars": min(sizes), "max_chars": max(sizes),
                  "too_short": sum(s < MIN_CHARS for s in sizes), "too_long": sum(s > MAX_CHARS for s in sizes),
                  "empty": sum(s == 0 for s in sizes), "exact_duplicates": dup,
                  "metadata_inheritance": round(inherit_ok, 3)})
    for c in chunks[:3]:
        samples.append({"chunk_method": method, "chunk_id": c["chunk_id"], "char_count": c["char_count"],
                        "content": c["content"].replace("\n", " / ")[:200]})

for name, rows in [("chunk_stats.csv", stats), ("chunk_sample.csv", samples)]:
    with open(OUT_DIR / name, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
for s in stats:
    print(s)
