# A1-M2 CSV 기반 판정 규칙·트리 탐색 실습

## 이 프로젝트가 하는 일

개발팀이 보낸 `sample.html`을 사람이 미리 정의한 `rules.csv` 기준으로 검사합니다. `rule_tree.csv`는 검사할 규칙을 업무 분류별로 보여주는 탐색 목차입니다. 이 파일의 `file` + `rule_id`로 실제 규칙 원본에서 해당 행을 찾습니다.

- `rules.csv`: 규칙의 **단일 원본**. 8개 규칙(적용 7건, 검토 중 1건). YAML 사용하지 않습니다.
- `rule_tree.csv`: 부모-자식 트리 구조. leaf에 `file=rules.csv`와 `rule_id`를 기록합니다.
- `checker.py`: CSV를 Pydantic 검증 후 읽어 `sample.html`을 검사하고 `results.json`을 생성합니다.
- `tree_lookup.py`: 트리 노드 → 파일 → 규칙 ID 순서로 조회합니다.
- `test_project.py`: 규칙별 판정과 데이터 연결 자동 검증.
- `field_map.json`: 후속 RAG의 **본문/메타데이터** 필드 분류 제안.

## 실행

```powershell
python -m pip install -r requirements.txt
python tree_lookup.py --list
python tree_lookup.py --node N_COMP_LINK_001
python checker.py
python -m unittest -v
```

## 서로 다른 두 CSV의 역할

`rules.csv`: 프로그램이 검사할 **조건 + 사람·LLM이 읽을 설명·출처**를 함께 저장.

`rule_tree.csv`: 어떤 규칙이 어떤 상위 분류에 속하는지, 그 규칙의 원본 파일과 ID가 무엇인지를 기록. `parent_id`로 트리를 구성하며 `file`과 `rule_id`를 함께 참조합니다.

## 향후 RAG에서 본문과 메타데이터

- 본문 내용: `title`, `description`, `reason`, `limitation`
- 메타데이터: `rule_id`, `rule_version`, `status`, `scope`, `policy_id`, `wcag_ref`, `kwcag_ref`, `reference_url`, `selector`, `operator`, `attribute`, `values`, `effective_from`
- 트리 탐색/계층 메타데이터: `node_id`, `parent_id`, `file`, `rule_id`, 상위 경로 `path`(탐색 시 계산)

**주의:** `status=proposed`는 검사에 사용하지 않습니다. 웹 접근성 공식 인증이나 WCAG 완전한 적합 판정 도구가 아닙니다. `reference_url`은 관련 공식 문서를 참고하는 링크이지 검사 결과의 공식 승인 근거가 아닙니다.

향후 A1-M3에서 같은 CSV를 텍스트 검색에 사용하고, A2에서 임베딩·벡터 DB·RAG에 연결합니다. 긴 설명 자료가 생기면 다른 별도 문서로 확장할 수 있습니다. 이 실습은 Git·YAML·LLM을 사용하지 않습니다.
