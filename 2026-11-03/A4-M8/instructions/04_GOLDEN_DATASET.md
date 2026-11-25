# 04_GOLDEN_DATASET

## 목적
검색 결과를 평가할 정답 질문셋을 준비한다.

## 입력
- data/golden_dataset.json
- docs/
- data/metadata.csv

## Golden 항목
- query_id
- question
- query_type
- relevant_doc_ids
- required_metadata
- expected_keywords
- difficulty

## query_type 예
- region
- year
- product
- customer
- exact_code
- comparison
- semantic

## 작업
1. relevant_doc_ids가 실제 존재하는지 검증.
2. 질문과 정답 문서 내용이 실제로 대응하는지 검사.
3. query_type별 개수 집계.
4. outputs/golden_validation.csv 생성.

## 원칙
Golden Dataset을 자동으로 임의 수정하지 않는다.
문제가 있으면 검토 목록으로 출력한다.
