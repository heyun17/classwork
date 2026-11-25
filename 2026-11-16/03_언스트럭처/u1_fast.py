# U1. fast 전략: PDF 안의 글자만으로 요소 나누기 (AI 모델 없음, 빠름)
import time
from unstructured.partition.pdf import partition_pdf
from common import summarize, save_json

for pdf in ["가이드라인_발췌.pdf", "표샘플_어려움.pdf"]:
    start = time.time()
    elements = partition_pdf(pdf, strategy="fast", languages=["kor"])
    print(f"\n===== {pdf} (fast, {time.time() - start:.1f}초)")
    summarize(elements)
    titles = [e.text for e in elements if e.category == "Title"]
    print(f"Title {len(titles)}개 중 앞 10개:", titles[:10])
    save_json(elements, f"u1_fast_{pdf.replace('.pdf', '')}.json")
