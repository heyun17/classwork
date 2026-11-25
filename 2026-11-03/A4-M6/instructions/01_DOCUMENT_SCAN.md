# 01_DOCUMENT_SCAN

## 목적
RAG 이전에 docs/의 문서 구조를 먼저 파악한다.

## 작업
1. docs/ 하위 폴더와 .md 파일을 재귀 탐색한다.
2. 각 문서에서 H1/H2/H3를 추출한다.
3. 파일별 글자수, 섹션수, 폴더 경로를 수집한다.
4. outputs/document_inventory.csv 생성.
5. outputs/document_tree.txt 생성.
6. 문서 구조 이상(제목 없음, 빈 문서, 중복 파일명)을 검사한다.

## 완료 검증
- docs의 모든 .md가 inventory에 존재
- 누락 파일 0
- 빈 문서 0
