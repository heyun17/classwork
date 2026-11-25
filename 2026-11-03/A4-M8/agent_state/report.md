# Document Update Agent 실행 보고

6개 파일 중 5개를 승인 절차 포함해 RAG에 반영했고, 회의메모_1028.txt는 형식 요건 미달로 거부했습니다. FAQ와 2027 전략은 회귀가 확인됐으나 승인에 따라 반영했으며, 부산 기존 문서 수정 및 인천 신규 지역도 승인받았습니다.

| 파일 | 상태 | doc_id | 사유 |
|---|---|---|---|
| 회의메모_1028.txt | rejected |  | RAG 문서 형식 요건을 충족하지 않음: .md 확장자가 아니며 H1/H2 구조 및 최소 내용 요건에 미달. |
| 2026_광주_기업_노트북전략.md | committed | GWANGJU_2026_CORP_NOTEBOOK |  |
| 2026_부산_공공기관_노트북전략.md | committed | BUSAN_2026_PUBLIC_NOTEBOOK |  |
| 2026_서울_공공기관_노트북_FAQ.md | committed | SEOUL_2026_PUBLIC_NOTEBOOK_FAQ | Recall@3 0.9125 → 0.8833; MRR 0.95 → 0.825 |
| 2026_인천_시장현황.md | committed | INCHEON_2026_MARKET |  |
| 2027_서울_공공기관_노트북전략.md | committed | SEOUL_2027_PUBLIC_NOTEBOOK | MRR 0.95 → 0.925 |