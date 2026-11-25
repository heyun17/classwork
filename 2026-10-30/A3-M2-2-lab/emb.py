"""01 노트북에서 만든 임베딩 함수를 다른 노트북에서도 쓰려고 옮겨 둔 파일"""
import os
import numpy as np
import faiss

EMB_MODEL = os.getenv("EMB_MODEL", "intfloat/multilingual-e5-small")                    # 문장 → 384차원
RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")  # (질문, 문서) → 관련도 점수

_fe = None

def get_embedder():
    global _fe
    if _fe is None:
        from transformers import pipeline
        _fe = pipeline("feature-extraction", model=EMB_MODEL, device=-1)
    return _fe

def embed(texts, kind="passage"):
    """문장 목록 → (개수, 384) float32, 길이 1. e5 규칙: 질문은 kind='query', 문서는 'passage'"""
    outs = get_embedder()([f"{kind}: {t}" for t in texts])
    X = np.array([np.array(o[0]).mean(axis=0) for o in outs], dtype="float32")
    faiss.normalize_L2(X)
    return X
