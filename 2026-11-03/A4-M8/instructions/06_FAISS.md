# 06_FAISS

## 목적
동일 청크를 임베딩하여 Vector 검색 성능을 확인한다.

## 구현
- OpenAI text-embedding-3-small
- FAISS
- embedding cache 필수
- 이미 생성된 embedding은 재호출 금지

## 실험 규칙
K만 바꿀 때 Vector DB를 다시 만들지 않는다.

## 청킹 방식별
- heading
- fixed_300
- fixed_500_overlap_100

각 방식은 별도 FAISS index로 저장한다.

## 산출물
- outputs/faiss/<chunk_method>/index.faiss
- outputs/faiss/<chunk_method>/chunks.json
- outputs/vector_results.csv
