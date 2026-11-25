# U5. 01·02에서 직접 만든 결과와 Unstructured 결과 비교
import json
import os

def load(name):
    path = os.path.join("results", name)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None

MANUAL_HEADINGS = ["01 가이드라인 개요", "1 필요성 및 목적", "2 관련 근거", "3 적용 범위", "4 용어 정리"]   # 01 교안 결과

print("=== 제목 찾기: 가이드라인_발췌.pdf ===")
print("01 교안(서식 규칙):", len(MANUAL_HEADINGS), "개", MANUAL_HEADINGS)
for strategy in ["fast", "hi_res"]:
    data = load(f"u1_fast_가이드라인_발췌.json" if strategy == "fast" else "u3_hi_res_가이드라인_발췌.json")
    if data is None:
        print(f"{strategy}: 결과 파일 없음 (먼저 실행하세요)")
        continue
    titles = [d["text"] for d in data if d["type"] == "Title"]
    hit = [h for h in MANUAL_HEADINGS if any(h.replace(" ", "") in t.replace(" ", "") for t in titles)]
    print(f"{strategy}: Title {len(titles)}개, 01 교안 제목 {len(hit)}/{len(MANUAL_HEADINGS)}개 포함")

print("\n=== 표 찾기: 표샘플_어려움.pdf ===")
print("02 교안(pdfplumber): 표 4개 조각 → 3개 표 (표 2는 두 쪽 합침, 표 3은 text 전략)")
for name in ["u1_fast_표샘플_어려움.json", "u3_hi_res_표샘플_어려움.json"]:
    data = load(name)
    if data is None:
        print(f"{name}: 결과 파일 없음")
        continue
    tables = [d for d in data if d["type"] == "Table"]
    print(f"{name}: Table {len(tables)}개", [(d["metadata"].get("page_number"), d["text"][:25]) for d in tables])
