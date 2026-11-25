# 09_DASHBOARD

## 목적
청킹과 Retrieval 품질을 학습용 Dashboard에서 한눈에 확인한다.

## Streamlit 필수 화면

### 1. Overview
- 문서 수
- 청크 수
- Golden 질문 수
- 현재 검색 방식
- 현재 K
- Precision@K
- Recall@K
- Hit Rate@K
- MRR
- nDCG@K
- 평균 Latency

### 2. Chunk Monitor
- 청킹 방식 선택
- Chunk Size Distribution
- 평균/최소/최대 크기
- 너무 짧은/긴 청크 수
- 중복 청크
- 청크 샘플
- 원문 ↔ 청크 비교

### 3. Golden Dataset
- 질문 목록
- query_type
- difficulty
- relevant_doc_ids
- expected_keywords

### 4. Search Comparison
- 동일 질문에 BM25 / Vector / Metadata+BM25 / Hybrid 결과를 나란히 표시
- rank / score / chunk / doc_id
- 정답 여부 표시

### 5. K Experiment
- K=1,2,3,5,10 비교
- Precision / Recall / Hit Rate / MRR / nDCG / Latency / Context Size
- K별 선 그래프

### 6. Chunking Experiment
- heading / fixed_300 / fixed_500_overlap_100 비교
- 같은 K에서 지표 비교

### 7. Query Type Analysis
- region / year / product / customer / exact_code / comparison / semantic
- 유형별 지표

### 8. Failure Analysis
- 실패 질문
- 기대 문서
- 실제 Top-K
- 자주 잘못 등장하는 문서/청크
- score separation

### 9. Recommendation
- 현재 Golden Dataset 기준 추천 K
- 추천 청킹 방식
- 추천 검색 방식
- 추천 Hybrid weight
- 추천 근거 표시

## 설명 방식
각 지표 옆에 짧은 학습 설명을 표시한다.
예:
- Precision: 가져온 문서 중 정답 비율
- Recall: 찾아야 할 정답을 얼마나 놓치지 않았는가

## 주의
추천값은 현재 샘플/Golden Dataset에 대한 결과임을 화면에 표시한다.
