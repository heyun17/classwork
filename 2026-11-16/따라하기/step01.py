"""
step01 · PDF 불러오기

실행: 랭스미스 폴더에서  python 따라하기/step01.py
"""

from langchain_community.document_loaders import PyPDFLoader

# ─────────────────────────────────────────────
# 1. RAG 자료 준비
# ─────────────────────────────────────────────
PDF_PATH = "가이드라인_발췌.pdf"                        # 랭스미스 폴더에서 실행하므로 파일 이름만 씀
pages = PyPDFLoader(PDF_PATH).load()                  # PDF 1쪽 = Document 1개


if __name__ == "__main__":
    print("쪽 수:", len(pages))
    print("\n[1쪽 메타데이터]", pages[0].metadata)
    print("\n[1쪽 본문 앞부분]\n" + pages[0].page_content[:300])
