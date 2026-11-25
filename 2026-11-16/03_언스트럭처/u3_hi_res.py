# U3. hi_res 전략: 레이아웃 AI 모델로 제목·표를 인식 (첫 실행 때 모델 다운로드)
import time
from unstructured.partition.pdf import partition_pdf
from common import summarize, save_json, RESULTS

for pdf in ["가이드라인_발췌.pdf", "표샘플_쉬움.pdf", "표샘플_어려움.pdf"]:
    start = time.time()
    elements = partition_pdf(
        pdf,
        strategy="hi_res",                 # 쪽을 그림으로 바꿔 레이아웃 모델로 영역 탐지
        languages=["kor"],
        infer_table_structure=True,        # 표는 HTML 구조까지 복원 → metadata.text_as_html
    )
    print(f"\n===== {pdf} (hi_res, {time.time() - start:.1f}초)")
    summarize(elements, head=20)
    titles = [e.text for e in elements if e.category == "Title"]
    print(f"Title {len(titles)}개:", titles[:15])

    tables = [e for e in elements if e.category == "Table"]
    print(f"Table {len(tables)}개")
    with open(f"{RESULTS}/u3_tables_{pdf.replace('.pdf', '')}.html", "w", encoding="utf-8") as f:
        f.write('<meta charset="utf-8"><style>table{border-collapse:collapse;margin:12px 0}td,th{border:1px solid #999;padding:3px 6px}</style>')
        for i, t in enumerate(tables, 1):
            print(f"  [표 {i}] p{t.metadata.page_number} 글자: {t.text[:60]}")
            print(f"          HTML 앞부분: {(t.metadata.text_as_html or '')[:120]}")
            f.write(f"<h3>표 {i} (p{t.metadata.page_number})</h3>{t.metadata.text_as_html or '(HTML 없음)'}")
    save_json(elements, f"u3_hi_res_{pdf.replace('.pdf', '')}.json")
