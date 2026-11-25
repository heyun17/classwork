# EDR AI 트리아지 에이전트 실습 (2인 1조 · 3일)

> 모든 데이터와 문서는 실습용 가상 자료입니다.

## 읽는 순서

| 순서 | 문서 | 내용 |
|---|---|---|
| 1 | [`docs/prep/01_edr_soc_intro.md`](docs/prep/01_edr_soc_intro.md) | EDR과 보안관제 입문, 예시 알림, **역할 정하기** (🔍 기록 담당 / 📘 문서 담당) |
| 2 | [`docs/prep/01b_story_to_system.md`](docs/prep/01b_story_to_system.md) | 이야기를 부품으로, 고장 나는 곳 |
| 3 | [`docs/prep/02_troubleshooting.md`](docs/prep/02_troubleshooting.md) | 트러블슈팅 순서, 깨 보기, 런북, 고장 예상표 |
| 4 | [`docs/prep/03_references.md`](docs/prep/03_references.md) | 역할별 참고 링크 |
| 5 | [`docs/guide/00_overview.md`](docs/guide/00_overview.md) | 실습 안내: 역할, 작업 형태, 3일 흐름 |
| 6 | [`DAY1`](docs/guide/DAY1.md) · [`DAY2`](docs/guide/DAY2.md) · [`DAY3`](docs/guide/DAY3.md) | 일차별 따라하기 |
| 7 | [`docs/guide/INFRA_STAGES.md`](docs/guide/INFRA_STAGES.md) | 인프라 0~7단계: 직접 작성 + 깨 보기 |
| 8 | [`docs/guide/WORK_SPEC.md`](docs/guide/WORK_SPEC.md) | 작업 명세서: 사전 자료~3일차 체크리스트, 결과물, 완료 기준 |

## 자료

| 폴더 | 내용 | 주로 쓰는 사람 |
|---|---|---|
| [`data/telemetry/`](data/telemetry/) | 가상 회사 PC의 활동 기록 샘플 | 🔍 기록 담당 |
| [`data/kb/`](data/kb/README.md) | 대응 정책·플레이북 PDF 9종, RAG 평가 질문 21개 | 📘 문서 담당 |

## 팀 문서 (실습 중에 채움)

| 문서 | 언제 |
|---|---|
| `docs/CONTRACT.md` | 1일차: 도구 계약 |
| `docs/ARCHITECTURE.md` | 1일차: 에이전트 설계도 → 2일차: 배포 구성도 |
| `docs/DECISIONS.md` | 매일: 결정과 그 이유, 평가 점수 |
| `docs/RUNBOOK.md` | 깨 보기를 할 때마다 |
| `docs/CAPACITY.md` | 2일차: 인프라 2단계 전 |
| `docs/DEPLOYMENT.md`, `docs/POSTMORTEM.md` | 3일차 |
| `docs/teachback/` | 매일 마지막 |
| `docs/advanced/` | 3일차: 고도화 기록 |
