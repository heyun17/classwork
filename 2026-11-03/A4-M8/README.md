# Part3 - RAG Data & Retrieval Quality Monitoring

## 목표
여러 개의 Markdown 매출/지역 문서를 대상으로 데이터 품질, 청킹 품질, 검색 품질을 함께 검증한다.

이 Part의 목적은 "답변을 잘 만드는 것"보다 먼저
"검색이 잘 되는가"를 수치와 화면으로 확인하는 것이다.

## 전체 흐름
1. 문서 구조 확인
2. metadata.csv 확인
3. 청킹
4. 청킹 결과 샘플 검수
5. BM25 인덱스
6. FAISS Vector DB
7. Metadata + BM25 + Vector Hybrid 검색
8. Golden Dataset 평가
9. K 값 비교
10. 청킹 방식 비교
11. 실패 질문 분석
12. 품질 모니터링 Dashboard

## 폴더 구조
```text
Part3.rag_quality/
├─ CLAUDE.md
├─ README.md
├─ .project_state.json
│
├─ instructions/
│  ├─ 00_PROJECT.md
│  ├─ 01_DOCUMENT_SCAN.md
│  ├─ 02_METADATA.md
│  ├─ 03_CHUNKING.md
│  ├─ 04_GOLDEN_DATASET.md
│  ├─ 05_BM25.md
│  ├─ 06_FAISS.md
│  ├─ 07_HYBRID.md
│  ├─ 08_EVALUATION.md
│  └─ 09_DASHBOARD.md
│
├─ docs/
│  ├─ 서울/
│  ├─ 부산/
│  ├─ 광주/
│  └─ 대전/
│
├─ data/
│  ├─ metadata.csv
│  └─ golden_dataset.json
│
├─ src/
├─ outputs/
└─ requirements.txt
```

## 샘플 데이터 설계 의도
문서들은 일부러 서로 비슷하게 작성되어 있다.

예:
- 서울/부산/광주/대전 모두 "공공기관", "노트북", "조달"이 등장한다.
- 2025년과 2026년 문서가 함께 존재한다.
- 제품 코드(NB-SEOUL-26 등)는 정확 문자열 검색에 유리하다.
- 지역/연도/고객유형/제품/문서유형은 metadata filter에 적합하다.

따라서 Vector 검색만으로는 충분하지 않고
Metadata + BM25 + Vector의 역할 차이를 비교할 수 있다.

## 권장 실행 순서
Claude Code에 아래처럼 한 Step씩 요청한다.

```text
instructions/01_DOCUMENT_SCAN.md를 수행해
instructions/02_METADATA.md를 수행해
...
```

## 평가 기본
K 후보:
```text
1, 2, 3, 5, 10
```

검색 방식:
```text
BM25
Vector
Metadata + BM25
Hybrid
```

## 중요
K만 바꿀 때는 Vector DB를 다시 만들지 않는다.
청킹 방식을 바꿀 때만 청크/임베딩/Vector DB를 새로 만든다.
