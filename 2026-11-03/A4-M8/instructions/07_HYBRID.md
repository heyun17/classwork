# 07_HYBRID

## 목적
Metadata + BM25 + Vector를 결합한다.

## 검색 흐름
1. 질문에서 명확한 metadata 조건이 있으면 filter
2. BM25 검색
3. Vector 검색
4. score 정규화
5. Hybrid score 계산
6. Top-K 반환

## 기본 가중치
- BM25: 0.4
- Vector: 0.6

가중치는 config로 분리한다.

## 비교 대상
- BM25
- Vector
- Metadata+BM25
- Hybrid

## 산출물
- outputs/hybrid_results.csv
