# STEP 3. 탐지한 객체를 쪽 그림 위에 색깔 박스로 표시하기
import pymupdf

PDF_PATH = "가이드라인_발췌.pdf"
COLORS = {"text": (0, 0.35, 1), "image": (1, 0, 0), "drawing": (0, 0.6, 0)}   # RGB (0~1)

doc = pymupdf.open(PDF_PATH)
for page_no in (0, 3):                                    # 1쪽, 4쪽
    page = doc[page_no]
    boxes = []
    for b in page.get_text("dict")["blocks"]:
        kind = "text" if b["type"] == 0 else "image"
        boxes.append((kind, pymupdf.Rect(b["bbox"])))
    for d in page.get_drawings():
        boxes.append(("drawing", d["rect"]))

    for kind, rect in boxes:                              # 원본을 바꾸지 않도록 그림만 그림 (저장 안 함)
        page.draw_rect(rect, color=COLORS[kind], width=1.2)
    page.get_pixmap(dpi=110).save(f"detect_p{page_no + 1}.png")
    print(f"detect_p{page_no + 1}.png 저장 (박스 {len(boxes)}개)")
