"""운영 3 · 인덱스를 객체 저장소 모양으로 저장하고 다시 불러오기
outputs_m4/store/ 를 버킷이라고 보고, a5-rag/index/v<번호>/ 아래에 파일 세 개를 둔다.
  index.faiss   FAISS 인덱스 (faiss.serialize_index)
  chunks.jsonl  번호 → 조각 ID · 문서 ID · 소제목 (벡터 번호와 원문을 잇는 표)
  manifest.json 모델 · 차원 · 개수 · 만든 시각 · 파일 해시
사용 예) python m4_ops_store.py            # 새 버전으로 저장 → 다시 불러와 검색 결과 확인
        python m4_ops_store.py --list     # 저장된 버전 목록
"""
import argparse
import datetime
import hashlib
import json

import faiss
import numpy as np

from m4lib import OUT, build_embeddings, load_chunks, questions, unit

ap = argparse.ArgumentParser()
ap.add_argument("--list", action="store_true")
ap.add_argument("--bucket", default="outputs_m4/store", help="버킷으로 쓸 폴더")
a = ap.parse_args()
from pathlib import Path

BUCKET = Path(a.bucket) if Path(a.bucket).is_absolute() else OUT.parent / a.bucket
PREFIX = BUCKET / "a5-rag" / "index"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


if a.list:
    for v in sorted(PREFIX.glob("v*")):
        m = json.loads((v / "manifest.json").read_text(encoding="utf-8"))
        print(f"{v.relative_to(BUCKET).as_posix()}  · {m['created']} · {m['model']} · {m['count']}개")
        for f in sorted(v.iterdir()):
            print(f"    {f.name:<14}{f.stat().st_size:>10,} bytes")
    raise SystemExit

E = build_embeddings()
X, Q = unit(E["chunk_vecs"]), unit(E["q_vecs"])
by_id = {c["chunk_id"]: c for c in load_chunks()}
index = faiss.IndexIDMap2(faiss.IndexFlatIP(X.shape[1]))
index.add_with_ids(X, np.arange(len(X), dtype="int64"))

ver = len(list(PREFIX.glob("v*"))) + 1
d = PREFIX / f"v{ver}"
d.mkdir(parents=True)
(d / "index.faiss").write_bytes(faiss.serialize_index(index).tobytes())
with open(d / "chunks.jsonl", "w", encoding="utf-8") as f:
    for n, cid in enumerate(E["chunk_ids"]):
        f.write(json.dumps({"n": n, "chunk_id": cid, "doc_id": by_id[cid]["doc_id"], "section": by_id[cid].get("section")}, ensure_ascii=False) + "\n")
manifest = {"version": ver, "created": datetime.datetime.now().isoformat(timespec="seconds"), "model": E["info"]["model"],
            "dims": int(X.shape[1]), "count": int(index.ntotal), "index_type": "IndexIDMap2(IndexFlatIP)", "chunking": "section",
            "files": {f: sha(d / f) for f in ("index.faiss", "chunks.jsonl")}}
(d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"저장: {a.bucket}/{d.relative_to(BUCKET).as_posix()}")
for f in sorted(d.iterdir()):
    print(f"   {f.name:<14}{f.stat().st_size:>10,} bytes")

# 다른 서버가 내려받았다고 가정하고 다시 읽는다
m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
ok = all(sha(d / f) == h for f, h in m["files"].items())
loaded = faiss.deserialize_index(np.frombuffer((d / "index.faiss").read_bytes(), dtype="uint8"))
table = [json.loads(l) for l in (d / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
print(f"\n불러오기 · 파일 해시 확인 {'통과' if ok else '실패'} · 모델 {m['model']} · {loaded.ntotal}개")
qi = [q["id"] for q in questions()].index("Q-017")
_, I1 = index.search(Q[qi:qi + 1], 3)
_, I2 = loaded.search(Q[qi:qi + 1], 3)
print(f"Q-017 상위 3 · 저장 전 {[table[j]['chunk_id'] for j in I1[0]]} · 불러온 뒤 {[table[j]['chunk_id'] for j in I2[0]]}")
print(f"같은 결과: {list(I1[0]) == list(I2[0])}")
