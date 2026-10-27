# 주문 보고서 개발 하네스 계약

## 목적
`report.py`에 `min_total` 필터를 추가하고, 기본 집계 동작을 유지한다.

## 수정 경계
- 변경 허용: `report.py` (정당한 이유가 있을 경우 테스트 추가 제안)
- 변경 금지: `orders.csv`, `data/source.sha256`, `data/expected.json`, `tests/test_report.py`
- `reference_solution/`은 정답 비교용이며 구현할 때 복사하지 않는다.

## 완료 기준
1. 기본 실행은 주문 4건·총액 17,000원을 반환한다.
2. `min_total=5000`이면 O101·O103만 출력한다(11,000원).
3. 음수 `min_total`은 ValueError로 거부한다.
4. `python -m unittest discover -s tests -v`가 통과한다.
5. 원본 CSV의 SHA-256 값은 작업 전후 동일하다.

## 실행 안전성
- 변경 금지 파일을 수정해야 한다면 이유를 적고 사용자 승인을 받는다.
- 검증 에이전트는 기본적으로 파일을 수정하지 않고 실패 증거를 보고한다.
- 테스트 실패 시 완료라고 보고하지 않는다.
