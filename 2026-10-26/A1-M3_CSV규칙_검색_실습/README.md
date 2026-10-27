# A1-M3: 규칙 CSV 기반 BoW·TF-IDF·BM25 정보검색

## A1-M2와 동일한 자료
- `data/rules.csv`: A1-M2에서 만든 규칙 원본. 새 지식 이력 CSV를 만들지 않음.
- `data/rule_tree.csv`: 부모·자식 관계 및 `file=rules.csv`, `rule_id` 연결.
- `data/sample.html`: A1-M2 검사 대상. M3에서는 HTML 판정기를 새로 구현하지 않음.

## 실행
```
python -m pip install -r requirements.txt
python 01_bow.py
python 02_tfidf_cosine.py
python 03_bm25_hand.py
python 04_csv_search.py
# 선택: python -m pip install rank-bm25
# 선택: python 05_bm25_library_optional.py
python -m unittest discover -s tests -v
```

## 학습 범위
- 01~03: 아주 짧은 3개 문서로 수치 계산과 벡터/랭킹 원리 익히기.
- 04: A1-M2의 **동일한** `rules.csv`와 `rule_tree.csv`에서 검색.
- 상태(`status=applied`)가 현재 정책인지 먼저 확인한 뒤 검색.
- 본문 = `title + description + reason + limitation`, 메타데이터 = `rule_id, rule_version, status, scope, policy_id, wcag_ref, kwcag_ref, reference_url, effective_from, source_file, node_id, parent_id, tree_path`.
- 문자 n-gram(2~3자)을 사용해 한국어 문장 형태 변화에 일부 대응하지만, 형태소 분석과 OOV는 **A1-M5**에서 별도로 다룸.
- 검색 점수 ≠ 공식 WCAG 적합 여부. 검사 엔진이 이미 반환한 상태를 바꾸지 않음.
- 문서 ID와 인용 출처를 포함한 검색 결과는 **A1-M4 평가**, **A1-M6 통합**, **A2 벡터/RAG**로 전달.

## 주의
- `rank_bm25()`의 양수 IDF는 설명용 Lucene 계열 변형이며 다른 패키지의 BM25Okapi IDF와 수치가 다를 수 있습니다. 같은 질의를 두 점수 체계의 절대값으로 직접 비교하지 마세요.
- `data/rules.csv`/`rule_tree.csv` 원본이 바뀌면 검색 인덱스를 다시 구축해야 하며, 실제 운영용 동기화·재색인은 A2에서 본격적으로 다룹니다.
- 이 모듈은 YAML, Git, LLM/API, 벡터 DB, LangChain을 도입하지 않습니다.

© 2026 부성순. All rights reserved. 외부 표준·라이브러리의 권리는 각 원저작자에게 있습니다.
