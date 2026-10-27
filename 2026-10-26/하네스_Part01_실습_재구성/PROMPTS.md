# Codex에 전달할 요청 (두 실험 폴더에서 반드시 동일하게 사용)

`report.py`의 `make_report(source, destination, min_total=0)`을 완성해 주세요.

1. 주문별 금액(`quantity * unit_price`)을 `output/report.csv`에 새 열 `total_amount`로 기록합니다.
2. `min_total=5000`이면 금액이 5,000원 이상인 주문만 출력합니다.
3. 기존 기본 동작을 유지하고 잘못된 입력(음수 수량·중복 주문 ID)을 처리합니다.
4. 최종적으로 수정 파일과 실제 실행한 검증 명령·결과를 보고해 주세요.

비교 실험이므로 미적용/적용 폴더에서 이 요청 문장을 바꾸지 않습니다.
