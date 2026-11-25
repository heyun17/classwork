# CLAUDE.md

## 프로젝트 목적
이 프로젝트는 매출/지역 문서 기반 RAG Data & Retrieval 품질을 검증하는 학습용 프로젝트다.

핵심 흐름:
문서 파악 → 메타데이터 → 청킹 → BM25 → FAISS → Hybrid → Golden Dataset 평가 → K/청킹 비교 → 대시보드

## 반드시 지킬 원칙
1. 새 코드를 작성하기 전에 기존 파일과 폴더를 먼저 확인한다.
2. 정상 동작하는 코드를 이유 없이 다시 작성하지 않는다.
3. 같은 기능을 하는 파일을 중복 생성하지 않는다.
4. 요청받은 Step에 필요한 파일만 생성/수정한다.
5. 완료된 Step은 다시 수행하지 않는다.
6. 기존 함수/모듈이 있으면 우선 재사용한다.
7. 불필요한 클래스, 프레임워크, 추상화 계층을 만들지 않는다.
8. LangChain은 사용하지 않는다.
9. Python 표준 라이브러리 + 최소 패키지 우선으로 구현한다.
10. 결과를 확인할 수 있는 출력/CSV/JSON을 남긴다.

## 토큰/코드 낭비 최소화
- 전체 프로젝트를 매번 다시 읽지 않는다.
- 필요한 파일만 읽는다.
- 이미 확인한 파일을 반복해서 읽지 않는다.
- 긴 설명 대신 변경 파일, 실행 명령, 검증 결과만 보고한다.
- 코드 전체를 응답에 재출력하지 않는다.
- README를 매 Step마다 다시 작성하지 않는다.
- 오류가 없으면 기존 파일을 건드리지 않는다.

## 재실행 규칙
- K만 변경: Vector DB 재생성 금지. 검색/평가만 다시 실행한다.
- Golden Dataset 변경: Vector DB 재생성 금지. 평가만 다시 실행한다.
- Hybrid weight 변경: Vector DB 재생성 금지. 검색/평가만 다시 실행한다.
- 청킹 방식 변경: 청크/임베딩/Vector DB 재생성 필요.
- 임베딩 모델 변경: 임베딩/Vector DB 재생성 필요.
- 문서 추가/삭제: 해당 문서 청킹/임베딩/인덱스 갱신 필요.

## 데이터 무결성
- docs/의 실제 문서 내용만 사용한다.
- 존재하지 않는 지역/연도/제품/코드/정책을 임의로 만들지 않는다.
- metadata.csv의 doc_id는 문서와 1:1 대응시킨다.
- 청크는 부모 문서의 metadata를 상속한다.
- Golden Dataset의 relevant_doc_ids는 실제 doc_id만 사용한다.

## 평가 기본값
- K 후보: 1, 2, 3, 5, 10
- 검색 방식: BM25 / Vector / Metadata+BM25 / Hybrid
- 기본 Hybrid 예시: BM25 0.4 + Vector 0.6
- Hybrid weight는 설정값으로 분리한다.

## 필수 평가 지표
- Precision@K
- Recall@K
- Hit Rate@K
- MRR
- nDCG@K
- Latency
- Context Size
- Chunk Size Distribution
- Duplicate/near-duplicate chunk 비율
- Score separation
- Metadata inheritance accuracy
- Retrieval coverage
- 질문 유형별 성능
- 실패 질문 분석

## 작업 방식
각 Step 시작 전:
1. .project_state.json 확인
2. 관련 입력 파일 확인
3. 재사용 가능한 기존 코드 확인

각 Step 종료 후:
1. 산출물 저장
2. 간단한 검증 실행
3. .project_state.json 갱신
4. 아래 형식으로만 보고

변경 파일:
- ...

실행 명령:
- ...

검증 결과:
- ...

다음 Step은 임의로 진행하지 않는다.
