# U2. LangChain UnstructuredLoader로 Document 만들기
from collections import Counter
from langchain_unstructured import UnstructuredLoader

loader = UnstructuredLoader("가이드라인_발췌.pdf", strategy="fast", languages=["kor"])
docs = loader.load()

print("Document 수:", len(docs))
print("category별:", dict(Counter(d.metadata["category"] for d in docs).most_common()))
print("메타데이터 키:", sorted(docs[0].metadata.keys()))
for d in docs[:6]:
    print(f"  p{d.metadata.get('page_number')} [{d.metadata['category']}] {d.page_content[:40]}")

# RAG에서 자주 쓰는 처리: 머리말(Header) 빼고, 제목 아래 내용끼리 묶기(chunk_by_title)
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

elements = [e for e in partition_pdf("가이드라인_발췌.pdf", strategy="fast", languages=["kor"])
            if e.category not in ("Header", "Footer")]
chunks = chunk_by_title(elements, max_characters=800, combine_text_under_n_chars=200)
print(f"\nchunk_by_title: 요소 {len(elements)}개 → 청크 {len(chunks)}개")
for c in chunks[:5]:
    print(f"  ({len(c.text)}자) {c.text[:60]}")
