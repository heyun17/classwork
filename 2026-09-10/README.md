# 환율 자료와 계산기

## 파일

- `환율_데이터.csv`: Frankfurter API에서 가져온 USD 기준 최신 환율 자료입니다.
- `환율계산기.html`: 같은 폴더의 CSV를 읽어 USD, EUR, JPY, KRW 사이의 금액을 계산합니다.

## 현재 자료

- API 기준일: `2026-09-09`
- 기준통화: `USD`
- 조회 통화: `EUR`, `JPY`, `KRW`
- 수집 시각: `2026-09-10 14:35:44 (KST)`

출처: <https://api.frankfurter.dev/v1/latest?from=USD&to=KRW,JPY,EUR>

## 실행 방법

1. `환율계산기.html`을 웹 브라우저로 엽니다.
2. 웹 서버로 열면 `환율_데이터.csv`를 자동으로 읽습니다.
3. HTML을 파일 탐색기에서 직접 열어도 기본 CSV 스냅샷으로 통화 목록과 계산기가 먼저 표시됩니다. 최신 CSV를 반영하려면 화면 아래의 CSV 파일 선택에서 `환율_데이터.csv`를 선택합니다.

## 날짜별 자료 추가

향후 환율을 추가할 때는 CSV에 같은 열 순서로 행을 덧붙입니다.

```csv
rate_date,fetched_at,base_currency,quote_currency,rate,amount,source_url
2026-09-10,2026-09-11T09:00:00+09:00,USD,EUR,0.86000,1,"https://api.frankfurter.dev/v1/latest?from=USD&to=KRW,JPY,EUR"
```

계산기는 `rate_date`와 `fetched_at`이 더 최근인 행을 통화별 최신값으로 사용하므로, 이후 차트에서 날짜별 환율 변동을 그릴 수 있습니다.
