"""A5-M4 실습 공통 코드 — OpenAI 임베딩 + FAISS.

- 검색 단위는 M1에서 만든 조각(소제목 단위) 196개: FAQ 80 + 정책 116.
- 임베딩은 OpenAI API로 한 번만 만들고 outputs_m4/embeddings.npz에 저장한다.
  파일이 있으면 다시 부르지 않는다 (--refresh로 새로).
"""
import json
import os
import time
from pathlib import Path

import numpy as np

from m1lib import load_faq, load_policies, make_chunks, match  # noqa: F401
from m2lib import load_env

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs_m4"
EMB = OUT / "embeddings.npz"
load_env()
EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL") or "text-embedding-3-small"


def load_chunks():
    return make_chunks(load_faq() + load_policies(), "section")


def questions():
    return json.loads((ROOT / "design" / "answers.json").read_text(encoding="utf-8"))["questions"]


def embed_texts(texts, batch=100):
    from openai import OpenAI  # pip install openai

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    vecs, tokens = [], 0
    for i in range(0, len(texts), batch):
        r = client.embeddings.create(model=EMBED_MODEL, input=texts[i:i + batch])
        vecs += [d.embedding for d in r.data]
        tokens += r.usage.total_tokens
    return np.array(vecs, dtype="float32"), tokens


def build_embeddings(refresh=False):
    """조각 196개 + 질문 7개를 한 번에 임베딩해 저장한다."""
    chunks, qs = load_chunks(), questions()
    if EMB.exists() and not refresh:
        return load_embeddings()
    t0 = time.time()
    cv, t1 = embed_texts([c["text"] for c in chunks])
    qv, t2 = embed_texts([q["question"] for q in qs])
    OUT.mkdir(exist_ok=True)
    np.savez(EMB, chunk_ids=np.array([c["chunk_id"] for c in chunks]), chunk_vecs=cv,
             q_ids=np.array([q["id"] for q in qs]), q_vecs=qv,
             info=np.array(json.dumps({"model": EMBED_MODEL, "tokens": t1 + t2, "seconds": round(time.time() - t0, 1)})))
    return load_embeddings()


def load_embeddings():
    z = np.load(EMB)
    info = json.loads(str(z["info"]))
    return {"chunk_ids": [str(x) for x in z["chunk_ids"]], "chunk_vecs": z["chunk_vecs"], "q_ids": [str(x) for x in z["q_ids"]], "q_vecs": z["q_vecs"], "info": info}


def unit(v):
    """코사인 유사도를 내적으로 계산하려고 길이를 1로 맞춘다."""
    v = np.array(v, dtype="float32")
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def hit(expected, doc_ids):
    return len(set(expected) & set(doc_ids))


# ------------------------------------------------------------------ 임베딩 캐시
import hashlib  # noqa: E402

CACHE = OUT / "cache"


def cache_key(text, model=None):
    """캐시 열쇠 = 모델 이름 + 글 내용의 해시. 글이 한 글자라도 바뀌거나 모델이 바뀌면 다른 열쇠가 된다."""
    return hashlib.sha256(f"{model or EMBED_MODEL}\n{text}".encode("utf-8")).hexdigest()[:20]


def load_cache():
    p = CACHE / "vectors.npz"
    if not p.exists():
        return {}
    z = np.load(p)
    return {k: z[k] for k in z.files}


def save_cache(cache):
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE / "vectors.npz", **cache)


def seed_cache_from_embeddings():
    """이미 만든 embeddings.npz의 벡터로 캐시를 채운다 (API 호출 없음)."""
    E = load_embeddings()
    texts = {c["chunk_id"]: c["text"] for c in load_chunks()}
    qs = {q["id"]: q["question"] for q in questions()}
    cache = load_cache()
    for cid, v in zip(E["chunk_ids"], E["chunk_vecs"]):
        cache[cache_key(texts[cid], E["info"]["model"])] = v
    for qid, v in zip(E["q_ids"], E["q_vecs"]):
        cache[cache_key(qs[qid], E["info"]["model"])] = v
    save_cache(cache)
    return cache


def embed_with_cache(texts, apply=False, model=None):
    """캐시에 있으면 꺼내 쓰고, 없는 것만 API로 임베딩한다. apply=False면 무엇을 임베딩할지만 알려 준다."""
    cache = load_cache()
    keys = [cache_key(t, model) for t in texts]
    miss = [i for i, k in enumerate(keys) if k not in cache]
    tokens = 0
    if miss and apply:
        vecs, tokens = embed_texts([texts[i] for i in miss])
        for i, v in zip(miss, vecs):
            cache[keys[i]] = v
        save_cache(cache)
    vecs = [cache.get(k) for k in keys]
    return vecs, {"total": len(texts), "hit": len(texts) - len(miss), "miss": miss, "tokens": tokens}
