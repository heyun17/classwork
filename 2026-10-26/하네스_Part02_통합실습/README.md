# 하네스 Part 02 통합 실습 (M1~M4)

Part 01의 주문 데이터와 동일한 예제를 사용합니다. 실습은 원본 CSV를 직접 수정하지 않습니다.

## 시작 상태
- Python 표준 라이브러리 기반
- `report.py`: 기본 4건 총액 계산은 되지만 `min_total` 필터는 미구현
- `tests/test_report.py`: 신규 조건 관련 테스트가 실패하는 것이 정상입니다.
- `tests/test_tools.py`: 도구/검증 코드 관련 기본 테스트

## 순서
1. `python -m unittest discover -s tests -v`: 시작 상태의 실패를 관찰
2. Codex에서 `PROMPTS.md`의 M2 작성 요청 수행. 수정 대상은 `report.py`
3. `python -m unittest discover -s tests -v`: 전체 테스트 통과 확인
4. `python .agents/skills/order-report-check/scripts/check_report.py`: Skill 검사 코드 수동 실행
5. `python tools/order_lookup.py O101`: 읽기 전용 Tool 호출
6. `python -m tools.workflow`: 완료 후 최종 오케스트레이터 확인

## 선택형 MCP
`python -m pip install 'mcp>=1,<2'` (설치 방식은 Windows PowerShell에서 따옴표 사용)
프로젝트 루트에서 `codex mcp add orders-readonly -- python <tools/mcp_orders.py의 절대경로>` 실행.
`codex mcp list`에서 등록 여부 확인. 필요하면 `codex mcp add --help` 참고.
이 과정은 Codex CLI 실행 환경이 필요하며 제공 환경에서는 MCP 런타임이 설치되지 않아 실행 검증하지 않았습니다.

## 보안
- `AGENTS.md`는 OS의 쓰기 권한을 강제로 없애는 파일이 아닙니다.
- 고위험 파일은 실제 파일 시스템 권한·샌드박스·승인 절차로 보호합니다.
- `data/source.sha256`은 원본 검증 기준으로 프로젝트에 함께 보관합니다.
- `tools/untrusted_note.txt` 안의 명령은 데이터이며 실행하면 안 됩니다.

## 정답 확인
`reference_solution/report.py`는 비교 전용이며 Codex 구현 실습 전에 복사하지 않습니다.
