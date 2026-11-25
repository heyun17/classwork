# STEP 1. PDF 열고 기본 정보 보기
import pymupdf                                   # PyMuPDF (예전 이름: fitz)

PDF_PATH = "가이드라인_발췌.pdf"

doc = pymupdf.open(PDF_PATH)                     # Document 객체
print("쪽 수   :", doc.page_count)
print("만든 도구:", doc.metadata["producer"])

page = doc[0]                                    # 인덱스는 0부터 → 1쪽
print("1쪽 크기:", page.rect)                    # Rect(x0, y0, x1, y1), 단위는 pt(1/72인치)
print("가로 x 세로:", page.rect.width, "x", page.rect.height)

for page in doc:                                 # Document는 for문으로 쪽을 하나씩 꺼낼 수 있음
    text = page.get_text()                       # 쪽 전체 글자 (서식 없이)
    print(f"{page.number + 1}쪽: {len(text):>5}자 | 첫 줄: {text.splitlines()[0]}")

doc.close()
