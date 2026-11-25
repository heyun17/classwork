# ====================================================================
# 파일 용도: Markdown 청킹, 임베딩 생성, FAISS 저장·불러오기·유사도 검색을 담당합니다.
# ====================================================================

import json
import re

import faiss
import numpy as np

from config import (
    MD_PATH,
    FAISS_DIR,
    FAISS_INDEX_PATH,
    CHUNKS_PATH,
    EMBEDDING_MODEL,
)

def read_markdown():
    return MD_PATH.read_text(
        encoding="utf-8"
    )

def chunk_markdown(text):
    parts = re.split(
        r"\n(?=## )",
        text
    )

    chunks = [
        part.strip()
        for part in parts
        if part.strip().startswith("## ")
    ]

    return chunks

def make_embeddings(openai_client, chunks):
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=chunks
    )

    vectors = np.array(
        [
            item.embedding
            for item in response.data
        ],
        dtype="float32"
    )

    faiss.normalize_L2(vectors)

    return vectors

def save_faiss(chunks, vectors):
    FAISS_DIR.mkdir(
        exist_ok=True
    )

    index = faiss.IndexFlatIP(
        vectors.shape[1]
    )

    index.add(vectors)

    faiss.write_index(
        index,
        str(FAISS_INDEX_PATH)
    )

    CHUNKS_PATH.write_text(
        json.dumps(
            chunks,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return index

def load_faiss():
    index = faiss.read_index(
        str(FAISS_INDEX_PATH)
    )

    chunks = json.loads(
        CHUNKS_PATH.read_text(
            encoding="utf-8"
        )
    )

    return index, chunks

def search_faiss(
    openai_client,
    question,
    k=3
):
    index, chunks = load_faiss()

    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=question
    )

    query_vector = np.array(
        [
            response.data[0].embedding
        ],
        dtype="float32"
    )

    faiss.normalize_L2(
        query_vector
    )

    scores, indices = index.search(
        query_vector,
        min(k, index.ntotal)
    )

    results = []

    for rank, idx in enumerate(indices[0]):
        results.append({
            "rank": rank + 1,
            "score": float(scores[0][rank]),
            "title": chunks[idx].splitlines()[0],
            "content": chunks[idx]
        })

    return results
