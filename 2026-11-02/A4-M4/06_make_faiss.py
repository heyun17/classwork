# ====================================================================
# 파일 용도: Markdown 청크를 임베딩하고 FAISS 벡터DB(index.faiss, chunks.json)로 저장합니다.
# ====================================================================

from clients import get_openai_client
from faiss_service import (
    read_markdown,
    chunk_markdown,
    make_embeddings,
    save_faiss,
)

openai_client = get_openai_client()

text = read_markdown()

chunks = chunk_markdown(
    text
)

vectors = make_embeddings(
    openai_client,
    chunks
)

index = save_faiss(
    chunks,
    vectors
)

print("FAISS 저장 완료")
print("청크 수:", len(chunks))
print("벡터 수:", index.ntotal)
print("벡터 차원:", index.d)
