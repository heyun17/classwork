# 공통: 결과 폴더와 요소 요약 출력 함수
import json
import os
from collections import Counter

os.environ.setdefault("UNSTRUCTURED_DISABLE_NOTICE", "1")   # 광고 문구 끄기
RESULTS = "results"
os.makedirs(RESULTS, exist_ok=True)


def summarize(elements, head: int = 15) -> None:
    """요소 종류별 개수와 앞부분 미리 보기"""
    print("요소 수:", len(elements))
    print("종류별:", dict(Counter(e.category for e in elements).most_common()))
    for e in elements[:head]:
        print(f"  p{e.metadata.page_number} {e.category:<15} {e.text[:45]}")


def save_json(elements, name: str) -> None:
    """요소 리스트를 JSON으로 저장 (results/이름.json)"""
    data = [e.to_dict() for e in elements]
    with open(os.path.join(RESULTS, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("저장:", os.path.join(RESULTS, name))