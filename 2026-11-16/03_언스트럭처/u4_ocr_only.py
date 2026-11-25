# U4. ocr_only 전략: 글자 정보를 쓰지 않고 쪽 그림을 OCR로 읽기 (스캔 PDF용)
import time
from unstructured.partition.pdf import partition_pdf
from common import summarize, save_json

pdf = "표샘플_쉬움.pdf"
start = time.time()
elements = partition_pdf(pdf, strategy="ocr_only", languages=["kor"])   # tesseract 한국어(kor) 필요
print(f"===== {pdf} (ocr_only, {time.time() - start:.1f}초)")
summarize(elements, head=20)
save_json(elements, "u4_ocr_only_표샘플_쉬움.json")
