# A1-M4 · M2 규칙 판정과 M3 정보검색의 성능 평가

## 무엇을 평가하나?

A1-M2의 판정 함수와 A1-M3의 검색 함수를 **변경하지 않고 재사용**합니다.

- **탐지:** `(target, rule_id)` 단위의 `passed`/`failed` 예측을 교육용 검토 정답과 비교하여 TP·FP·FN·TN, Precision·Recall·F1을 산출합니다. `cantTell`과 `inapplicable`은 별도 집계하고 판정 커버리지를 기록합니다.
- **검색:** `gold/search_gold.csv`의 질문별 관련 규칙 ID와 M3 TF-IDF·BM25의 순위를 대조하여 Recall@k·Hit@k·MRR@k·nDCG@k를 계산합니다. `k=1,2,3`을 비교합니다.

이 데이터는 교육용 예제로 **공식 웹 접근성 인증·실서비스 정확도 검증을 의미하지 않습니다.** 탐지 검토 정답은 제공된 샘플 HTML의 지원 검사 조건에 맞춰 편집된 것이므로 높은 점수를 일반화할 수 없습니다.

## A1-M2/M3 입력 자료 연속성

`data/rules.csv`, `data/rule_tree.csv`, `data/sample.html`은 A1-M2 개정본의 파일을 내용 변경 없이 그대로 복사했습니다. A1-M3도 같은 두 CSV를 사용합니다. 

- `checker.py`: A1-M2 CSV 직접 판정기 코드 그대로.
- `search_engine.py`: A1-M3 정보검색 코드 그대로.
- **새 규칙/새 RAG 지식 CSV, YAML, 규칙 이력 CSV, Git 실습은 도입하지 않습니다.**
- `gold/detection_gold.csv`, `gold/search_gold.csv`: 성능을 확인하기 위한 **별도 평가 정답셋**이며 규칙 엔진 입력이나 RAG 지식 원본이 아닙니다.

적용 상태 `applied`인 **규칙 7개만** 판정·검색 기본 대상으로 사용합니다. `proposed` 규칙 1개는 현재 정책의 검색/평가 대상이 아닙니다.

## 실행 순서

Windows PowerShell, 가상환경에서 ZIP을 해제한 다음:

```powershell
python -m pip install -r requirements.txt
python 01_basics_detection.py
python 02_basics_retrieval.py
python 03_eval_m2_checker.py
python 04_eval_m3_search.py
python 05_generate_report.py
python -m unittest discover -s tests -v
```

`05_generate_report.py`는 규칙·트리·샘플·정답셋 SHA-256 해시(앞 12자리), 탐지 결과와 검색 평가를 `report.json`으로 저장합니다.

## 평가 결과 (제공 샘플)

- M2 적용 규칙 7건 → 검사 결과 29건.
- 22건 교육용 검토 정답의 상태 일치율 100%, 그중 `cantTell` 4건. 확정 정답 18건의 TP 7, FP 0, FN 0, TN 11. **이는 샘플 기반 자체 검사 조건 일치율이지 WCAG 적합성·현장 정확도 100%가 아닙니다.**
- M3 질문 7개 기준 TF-IDF·BM25 모두 이 샘플에서는 Recall@1≈78.6%, Recall@2=100%, MRR@2≈92.9%. 검색 데이터 규모와 정답셋이 작으므로 두 알고리즘의 일반적인 동등 성능을 주장할 수 없습니다.
- Q02 `더보기 사내 링크 금지`는 두 검색기 모두 실제 관련 규칙 `COMP-LINK-001`이 2위에 나타나는 예제입니다.
- 검색 점수 절대값(TF-IDF 코사인 vs BM25 점수)은 직접 비교하지 않습니다.

## 실습 자료 구성

| 파일 | 역할 |
| --- | --- |
| `metrics.py` | 이진 분류·검색 순위 평가 계산 함수 |
| `gold/detection_gold.csv` | `(target, rule_id)`와 검토 결과, 사유 |
| `gold/search_gold.csv` | 질문별 관련 규칙 ID 목록 |
| `01_basics_detection.py` | TP=4 FP=2 FN=1 TN=3 손계산 확인 |
| `02_basics_retrieval.py` | Recall@k·Hit@k·RR@k·nDCG@k 개념 실습 |
| `03_eval_m2_checker.py` | M2 실제 검사 출력과 검토 정답 대조 |
| `04_eval_m3_search.py` | M3 실제 TF-IDF·BM25 검색 순위 평가 |
| `05_generate_report.py` | JSON 평가 결과 생성 및 입력 해시 기록 |
| `tests/test_eval.py` | 자동 테스트 |

## 다음 단계와의 관계

A1-M5의 텍스트 전처리·형태소 분석, A1-M6의 규칙 검사/검색 통합, A2의 벡터 DB·RAG 평가 단계에서도 **같은 평가 설계와 규칙 ID·출처 메타데이터**를 재사용할 수 있습니다.

© 2026 부성순. All rights reserved. W3C 등 외부 표준 및 라이브러리 저작권은 각 원저작자에게 있습니다.
