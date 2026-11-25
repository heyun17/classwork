"""
step02 · 청크로 자르기

실행: 랭스미스 폴더에서  python 따라하기/step02.py
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ─────────────────────────────────────────────
# 1. RAG 자료 준비
# ─────────────────────────────────────────────
PDF_PATH = "가이드라인_발췌.pdf"                        # 랭스미스 폴더에서 실행하므로 파일 이름만 씀
pages = PyPDFLoader(PDF_PATH).load()                  # PDF 1쪽 = Document 1개

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(pages)              # 쪽 → 500자 조각 (메타데이터는 그대로 따라감)


if __name__ == "__main__":
    print(f"{len(pages)}쪽 → {len(chunks)}개 청크")
    for c in chunks[:3]:
        print("\n---", f"p.{c.metadata['page'] + 1}", f"({len(c.page_content)}자)")
        print(c.page_content[:120])
