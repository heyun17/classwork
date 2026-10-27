# Part 02 · M1-03 — 입력·산출물·오류 계약 독립 검증 실습

Part 02의 기존 주문 보고서 프로젝트를 이어받되, **M1-03에서는 Codex 에이전트 설정을 만들지 않습니다.** 그 전에 어떤 요청과 산출물을 `PASS/BLOCK`할지 Python으로 검증합니다. TOML·Skill·MCP는 이후 모듈에서 사용합니다.

## 실행 방법

압축을 풀고 `하네스_Part02_통합실습` 프로젝트 루트에서 실행합니다.

```shell
python -m contract_lab.demo
python -m unittest discover -s contract_lab/tests -v
```

검증 코드는 Python 표준 라이브러리만 사용합니다. 현재 **자동 테스트 20개**가 통과합니다.

## 어떤 파일이 무엇을 하는가?

| 파일 | 역할 |
| --- | --- |
| `../orders.csv` | 신뢰하는 주문 원본. 쓰지 않습니다 |
| `../data/expected.json` | `min_total=5000`인 기본 시나리오의 고정 회귀 정답 |
| `fixtures/request_ok.json` | 유효한 요청 데이터. `min_total` 값이 기대 주문을 결정합니다 |
| `fixtures/candidates.json` | PASS 1건과 BLOCK 8건의 후보 완료 보고 |
| `fixtures/filtered_ok.csv` | 최소금액 5000 기준 정상 산출물 |
| `fixtures/filtered_6000.csv` | 최소금액 6000 기준 정상 산출물 |
| `fixtures/filtered_offset.csv` | 개별 행 금액이 모두 틀려도 합계만 11000인 위험 사례 |
| `fixtures/filtered_duplicate.csv` | 중복 주문 ID를 포함한 잘못된 결과 |
| `contracts.py` | 입력 계약·출력 경로·개별 행·업무 정답·원본 보존 검증 |
| `demo.py` | 실제 9개 후보와 변경된 임계값 2개를 출력 |
| `tests/test_contracts.py` | 기본 테스트 12개 및 재발 방지 회귀 테스트 8개 |

## 무엇을 검증하는가?

- 에이전트가 `ok: true`를 선언해도 **실제 CSV의 각 주문·금액·건수·합계**를 검사합니다.
- `min_total=5000`이면 O101/O103, `6000`이면 O101, `10000`이면 결과가 없어야 합니다.
- 5000원 기준의 고정 정답을 6000원/10000원 요청에 재사용하지 않습니다.
- `source_file`과 `artifact_path`를 허용된 파일·경로로 제한하며, 입력 구조 오류도 `BLOCK`으로 답합니다.
- `expected.json`은 기준 정답을 기록한 파일입니다. 테스트를 통과시키기 위해 **정답 파일을 결과에 맞춰 수정하면 안 됩니다**.

## 권장 실습 순서

1. `demo.py`를 실행해 `PASS/BLOCK`과 오류 코드를 읽습니다.
2. `filtered_ok.csv`와 `filtered_offset.csv`를 비교합니다. 두 파일의 총액이 같아도 행 값이 다릅니다.
3. `request_ok.json`의 `min_total`을 테스트용 사본에서 6000/10000으로 바꾸고 결과를 관찰합니다.
4. 기존 `contracts.py`의 검증 조건을 완화하지 말고 새 오류 후보와 테스트를 추가합니다.
5. `python -m unittest discover -s contract_lab/tests -v` 실행 로그를 확인합니다.

> 한계: 이 예제는 `orders.csv`와 `source.sha256`을 신뢰 가능한 기준으로 가정합니다. 실제 운영에서는 정답 원본·해시 기준을 누가 수정할 수 있는지에 대한 별도 권한·감사 설계가 필요합니다.
