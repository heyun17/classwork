# 00_PROJECT

## 목표
docs/의 Markdown 문서를 대상으로 데이터/청킹 품질과 검색 품질을 모니터링하는 시스템을 만든다.

## 완료조건
최종 Dashboard에서 아래를 확인할 수 있어야 한다.

- 문서 수 / 청크 수
- 청크 샘플
- Chunk Size Distribution
- Metadata 상속 상태
- Golden Dataset 질문 수
- BM25 / Vector / Metadata+BM25 / Hybrid 비교
- Precision@K
- Recall@K
- Hit Rate@K
- MRR
- nDCG@K
- Latency
- Context Size
- K별 비교
- 청킹 방식별 비교
- 질문 유형별 성능
- 실패 질문
- 과도하게 자주 검색되는 청크
- 추천 K / 추천 청킹 방식

## 구현 규칙
CLAUDE.md를 최우선으로 따른다.
