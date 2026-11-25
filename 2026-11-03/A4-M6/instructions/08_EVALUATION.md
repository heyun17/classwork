# 08_EVALUATION

## 목적
Golden Dataset으로 Retrieval 품질을 정량 평가한다.

## 필수 지표
### Precision@K
검색된 K개 중 정답 문서 비율.

### Recall@K
전체 정답 문서 중 검색된 정답 비율.

### Hit Rate@K
정답 문서가 Top-K 안에 하나라도 있으면 1.

### MRR
첫 번째 정답 문서 순위의 역수 평균.

### nDCG@K
관련 문서가 상위 순위에 잘 배치되는지 평가.

### Latency
질문 1건 검색 시간.

### Context Size
Top-K 청크 전체 글자수 또는 추정 토큰수.

## 추가 모니터링
- score separation: Top1 score - Top2 score
- retrieval coverage: 전체 정답 doc 중 한 번이라도 검색된 비율
- over-retrieved chunks: 지나치게 자주 등장하는 chunk
- duplicate top-k ratio
- metadata inheritance accuracy
- query_type별 성능
- difficulty별 성능
- 실패 질문 목록

## K 비교
K = 1, 2, 3, 5, 10

## 중요
K 변경 시 Vector DB 재생성 금지.

## 산출물
- outputs/evaluation_summary.csv
- outputs/evaluation_by_query.csv
- outputs/evaluation_by_type.csv
- outputs/k_comparison.csv
- outputs/failure_cases.csv
