# (강사용 · 학생 배포 전 삭제) 현재 상태와 다음 작업

## 완료된 것
- 사전 자료: `docs/prep/` 01, 01b, 02, 03
- 가이드: `docs/guide/` 00_overview, DAY1~3, INFRA_STAGES (역할: 🔍 기록 담당 / 📘 문서 담당, 시간 정보 없음)
- 자료: PDF 9종 + 설명서 + RAG 평가 질문 21개 (`data/kb/`), 샘플 기록 24줄 (`data/telemetry/`)
- 팀 문서 템플릿: `docs/*.md`, `docs/teachback/`

## 아직 없는 것: 코드
가이드가 가리키는 파일과 TODO입니다. 이 목록대로 만들면 가이드와 맞습니다.

### 채울 곳 (TODO)
| 번호 | 담당 | 일차 | 파일 | 내용 |
|---|---|---|---|---|
| `REC-1` | 🔍 | 1 | `src/soc/telemetry/index_template.py` | `edr-events-*` 인덱스 템플릿 |
| `REC-2` | 🔍 | 1 | `src/soc/telemetry/tools.py` | `get_process_tree` |
| `REC-3` | 🔍 | 1 | 〃 | `get_process_activity` |
| `REC-4` | 🔍 | 1 | 〃 | `get_host_timeline` |
| `DOC-1` | 📘 | 1 | `src/soc/kb/parse.py` | `partition()` 호출 |
| `DOC-2` | 📘 | 1 | 〃 | 머리말·꼬리말 제거 |
| `DOC-3` | 📘 | 1 | `src/soc/kb/chunk.py` | `chunk_by_title()` 값 |
| `DOC-4` | 📘 | 1 | `src/soc/kb/index.py` | `kb-playbooks` 매핑 |
| `DOC-5` | 📘 | 1 | `src/soc/kb/search.py` | RRF 결합 |
| `G-1` | 👥 | 2 | `src/soc/agent/guardrail.py` | 인용한 `event_id`가 실제 조회한 기록인지 |
| `G-2` | 👥 | 2 | 〃 | 악성 판정의 근거 2개 이상 |
| `H-1` | 👥 | 2 | `src/soc/agent/nodes.py` | 위험한 조치 → `interrupt()` |
| `H-2` | 👥 | 2 | `src/soc/agent/checkpoint.py` | `PostgresSaver` 연결 |
| `DIFY-1` | 👥 | 3 | `src/soc/api/dify.py` | 점수를 0~1로 정규화 |

### 제공할 파일 (TODO 없음)
| 파일·명령 | 가이드에서 쓰는 곳 |
|---|---|
| `src/soc/mocks.py` (가짜 도구 4개) | DAY1 1번 계약, 4번 뼈대 |
| `python -m soc.simulator.run --dump data/sim.jsonl` | DAY1 3-🔍-1 |
| `python -m soc.kb.inspect --strategy fast` | DAY1 3-📘-1 |
| `python -m soc.kb.ingest [--dry-run]` | DAY1 3-📘-2, 3-📘-3 |
| `python -m soc.eval.rag_eval` | DAY1 3-📘-4, DAY2 4번 |
| `python -m soc.agent.graph` (Mermaid 출력) | DAY1 4-2 |
| `python -m soc.eval.agent_eval --n 12` | DAY2 4번, DAY3 4번 |
| API: `POST /approvals/{alert_id}`, `/dify/retrieval` | DAY2 1-3, DAY3 2번 |
| 테스트: `test_telemetry_tools`, `test_graph_skeleton`, `test_guardrail` | DAY1, DAY2 |
| 탐지 룰 → `edr-alerts`에 `status=new`로 저장 (Kafka 없음) | INFRA 4단계 |
| `infra/` | **비워 둠** (학생이 작성). 강사용 정답 매니페스트는 별도 |

## 실습 전에 준비할 것: 팀 서버
팀마다 가비아 서버 1대를 만들어 1일차 전에 접속 정보를 나눠 줍니다.
- 사양: Ubuntu 22.04/24.04, vCPU 4 / 메모리 16GB / 디스크 50GB 이상, 공인 IP
- 계정: 팀원 2명의 SSH 공개키 등록, `sudo` 가능 (k3s 설치, sysctl, ufw에 필요)
- 가비아 콘솔 방화벽: 22, 80, 443 열기. 6443은 학생이 직접 열지 않으므로 **강사가 강의장 IP만** 열어 둠
- 설치는 하지 않음: k3s, Docker는 학생이 1단계에서 직접 설치
- GHCR: 학생 각자 GitHub 계정으로 push (PAT `write:packages`). 강사 준비 없음

## 실습 전에 확인할 것
1. 정답 코드와 정답 매니페스트로 가비아 서버에 0~7단계 전체를 한 번 배포
2. `hi_res` 첫 실행 때 모델 다운로드가 실습 네트워크에서 되는지 (안 되면 09번 표 고도화는 다른 방법으로)
3. OpenAI 키 배포 방식과 팀당 예산
4. 깨 보기 중 서버 권한이 필요한 것을 학생 계정으로 할 수 있는지: 2-1 커널 설정(sudo), 5-3 방화벽(서버의 ufw로 하게 함. 가비아 콘솔 방화벽 권한은 주지 않음)
