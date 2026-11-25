# ====================================================================
# 파일 용도: RAG 원문 Markdown이 어떤 청크로 분리되는지 임베딩 전에 확인합니다.
# ====================================================================

from faiss_service import (
    read_markdown,
    chunk_markdown,
)

text = read_markdown()

chunks = chunk_markdown(
    text
)

print("청크 수:", len(chunks))

for i, chunk in enumerate(chunks):
    print("\n" + "=" * 50)
    print("Chunk", i)
    print("=" * 50)
    print(chunk)
