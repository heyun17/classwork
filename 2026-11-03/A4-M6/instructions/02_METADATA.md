# 02_METADATA

## 목적
검색 전 필터링에 사용할 문서 메타데이터를 확정한다.

## 입력
- data/metadata.csv
- docs/

## 필수 필드
- doc_id
- year
- region
- customer_type
- product
- doc_type
- product_code
- source_file

## 작업
1. metadata.csv의 source_file이 실제 존재하는지 검증.
2. doc_id 중복 검사.
3. 필수 필드 누락 검사.
4. 문서 수와 metadata 행 수 1:1 확인.
5. outputs/metadata_validation.csv 생성.

## 중요
문서에서 추론해 metadata를 임의 변경하지 않는다.
제공된 metadata.csv를 기준으로 검증한다.
