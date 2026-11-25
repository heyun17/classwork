# 03_CHUNKING

## 목적
문서를 여러 청킹 방식으로 나누고 결과를 눈으로 비교한다.

## 청킹 방식
A. heading
- H2 단위 우선
- 너무 짧은 섹션은 인접 섹션과 병합 가능

B. fixed_300
- 약 300자 기준

C. fixed_500_overlap_100
- 약 500자
- overlap 약 100자

## 청크 필수 필드
- chunk_id
- doc_id
- chunk_method
- chunk_order
- content
- char_count
- source_file
- year
- region
- customer_type
- product
- doc_type
- product_code

## 산출물
- outputs/chunks_heading.json
- outputs/chunks_fixed_300.json
- outputs/chunks_fixed_500_overlap_100.json
- outputs/chunk_sample.csv
- outputs/chunk_stats.csv

## 검증
- 부모 metadata 상속 정확도 100%
- 빈 청크 0
- 지나치게 짧은 청크 수 표시
- 지나치게 긴 청크 수 표시
- 중복/near-duplicate 후보 표시
