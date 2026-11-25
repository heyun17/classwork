# STEP 5. 모든 span을 JSON으로 저장하기
import json
import pymupdf

PDF_PATH = "가이드라인_발췌.pdf"


def is_bold(span: dict) -> bool:
    """flags의 bold 비트 또는 글꼴 이름으로 굵은 글씨 판단"""
    return bool(span["flags"] & 16) or "bold" in span["font"].lower()


def extract_spans(pdf_path: str) -> list[dict]:
    records = []
    with pymupdf.open(pdf_path) as doc:          # with: 끝나면 자동으로 close
        for page in doc:
            blocks = page.get_text("dict", sort=True)["blocks"]   # sort=True: 위→아래, 왼→오른 순서
            for b_no, block in enumerate(blocks):
                if block["type"] != 0:
                    continue
                for l_no, line in enumerate(block["lines"]):
                    for span in line["spans"]:
                        text = span["text"]
                        if not text.strip():         # 공백만 있는 span은 버림
                            continue
                        records.append({
                            "page": page.number + 1,
                            "block": b_no,
                            "line": l_no,
                            "text": text,
                            "font": span["font"],
                            "size": round(span["size"], 1),
                            "bold": is_bold(span),
                            "color": f"#{span['color']:06x}",
                            "bbox": [round(v, 1) for v in span["bbox"]],
                        })
    return records


if __name__ == "__main__":
    spans = extract_spans(PDF_PATH)
    with open("spans.json", "w", encoding="utf-8") as f:
        json.dump(spans, f, ensure_ascii=False, indent=2)
    print(f"span {len(spans)}개 → spans.json 저장")
    for r in spans[:6]:                               # 앞부분 6개만 한 줄씩 미리 보기
        print(json.dumps(r, ensure_ascii=False))
