import pymupdf
from pathlib import Path


# =========================================================
# 1. PDF 열기
# =========================================================

PDF_PATH = "가이드라인_발췌.pdf"

doc = pymupdf.open(PDF_PATH)


# =========================================================
# 2. PyMuPDF 색상값을 "#RRGGBB" 형태로 변환
# =========================================================

def int_to_hex_color(color):
    return f"#{color & 0xFFFFFF:06x}"


# =========================================================
# 3. PDF의 텍스트를 dict 형태로 추출
#
# 결과 예:
# {
#     "page": 1,
#     "block": 3,
#     "line": 1,
#     "text": "필요성 및 목적",
#     "font": "MalgunGothicBold",
#     "size": 12.0,
#     "bold": True,
#     "color": "#009c97",
#     "bbox": [...]
# }
# =========================================================

elements = []

for page in doc:

    page_dict = page.get_text("dict")

    for block_idx, block in enumerate(page_dict["blocks"]):

        # 텍스트 블록만 사용
        if block["type"] != 0:
            continue

        for line_idx, line in enumerate(block["lines"]):

            for span in line["spans"]:

                text = span["text"].strip()

                if not text:
                    continue

                font = span["font"]
                flags = span["flags"]

                element = {
                    "page": page.number + 1,
                    "block": block_idx,
                    "line": line_idx,
                    "text": text,
                    "font": font,
                    "size": round(span["size"], 1),

                    # font 이름 또는 PyMuPDF bold flag로 판단
                    "bold": (
                        "bold" in font.lower()
                        or bool(flags & 16)
                    ),

                    "color": int_to_hex_color(span["color"]),
                    "bbox": [
                        round(v, 1)
                        for v in span["bbox"]
                    ]
                }

                elements.append(element)


# =========================================================
# 4. 소제목 판별
#
# 기준:
# font  = MalgunGothicBold
# size  = 12.0
# bold  = True
# color = #009c97
# =========================================================

def is_subheading(item):

    return (
        item["font"] == "MalgunGothicBold"
        and abs(item["size"] - 12.0) < 0.1
        and item["bold"] is True
        and item["color"].lower() == "#009c97"
    )


# =========================================================
# 5. 소제목 기준 청킹
#
# 소제목을 만나면 새 청크 시작
# 다음 소제목이 나오기 전까지 같은 청크에 포함
# =========================================================

chunks = []

current_title = None
current_text = []
start_page = None
end_page = None


for item in elements:

    text = item["text"]

    # ---------------------------------------------
    # 소제목 발견
    # ---------------------------------------------
    if is_subheading(item):

        # 이전 청크 저장
        if current_title is not None:

            chunks.append({
                "title": current_title,
                "page_start": start_page,
                "page_end": end_page,
                "text": "\n".join(current_text)
            })

        # 새 청크 시작
        current_title = text
        current_text = [text]

        start_page = item["page"]
        end_page = item["page"]

    # ---------------------------------------------
    # 일반 본문
    # ---------------------------------------------
    elif current_title is not None:

        current_text.append(text)
        end_page = item["page"]


# =========================================================
# 6. 마지막 청크 저장
# =========================================================

if current_title is not None:

    chunks.append({
        "title": current_title,
        "page_start": start_page,
        "page_end": end_page,
        "text": "\n".join(current_text)
    })


doc.close()


# =========================================================
# 7. 결과 확인
# =========================================================

print(f"전체 텍스트 요소: {len(elements)}개")
print(f"생성된 청크: {len(chunks)}개")


for i, chunk in enumerate(chunks, 1):

    print()
    print("=" * 70)
    print(f"CHUNK {i}")
    print(f"소제목 : {chunk['title']}")
    print(
        f"페이지 : {chunk['page_start']} ~ "
        f"{chunk['page_end']}"
    )
    print("-" * 70)

    print(chunk["text"])