# Part 02 · M1-04 — 실행 순서, 병렬 감사, 실패 전파·재시도

## 역할

M1-03에서는 **무엇을 받아 무엇으로 합격 판정할지** (`verify_delivery`)를 정의했습니다. 이번 M1-04에서는 **계약 검증이 실패할 때 다음 단계로 가지 않는 실행 구조**를 구성합니다. 이미 검증된 주문 보고서 후보(CSV fixture)를 읽기 전용으로 검토하며 실제 Codex 멀티에이전트 또는 Git 배포를 실행하지 않습니다.

## 시작 경로

전체 ZIP 압축 해제 후 `하네스_Part02_통합실습` 폴더에서 아래 명령을 실행합니다.

```powershell
python -m workflow_lab.demo --case pass
python -m workflow_lab.demo --case false_success_claim
python -m workflow_lab.demo --case bad_request
python -m workflow_lab.demo --case pass --fault temporary
python -m workflow_lab.demo --case pass --fault persistent
python -m workflow_lab.demo --case pass --fault invalid
python -m unittest discover -s workflow_lab/tests -v
```

## 주요 파일

- `workflow_lab/runner.py`: 실행 게이트·병렬 감사·제한된 재시도 로직
- `workflow_lab/demo.py`: 실행 파라미터와 로그 출력
- `workflow_lab/tests/test_workflow.py`: 10개 자동 테스트
- `contract_lab/contracts.py`: M1-03에서 검증한 기존 데이터 계약 (변경하지 않음)
- `contract_lab/fixtures`: 앞선 모듈에서 제공한 후보 산출물 (재사용)

## 단계

1. `intake`: 요청 구조 검사. 실패 → 뒤 단계 `SKIP`
2. `contract_gate`: 업무 정답·원본·산출물 검증. 실패 → 감사·승인 `SKIP`
3. `schema_review`, `source_review`: 계약 통과 시에만 두 독립 읽기 감사가 병렬 실행
4. `release_gate`: 모두 PASS일 때만 승인 판단. **실제 공개·DB 쓰기·배포는 수행하지 않음**

## 장애 재현

- `--case false_success_claim`: AI가 `ok: true`라고 주장하지만 산출물은 틀림 → 계약 BLOCK, 후속 SKIP
- `--case bad_request`: 요청 구조 오류 → intake BLOCK, 전부 SKIP
- `--fault temporary`: 일시 장애 1회 뒤 복구 → 최대 2회 이내 재시도해 PASS
- `--fault persistent`: 2회 시도 모두 실패 → 최종 BLOCK
- `--fault invalid`: 논리/계약 오류이므로 재시도 없이 BLOCK

**주의:** 병렬 실행은 읽기 전용 검사이므로 안전하게 비교할 수 있습니다. 한 병렬 작업이 실패해도 이미 시작한 다른 작업이 즉시 강제 중단되는 것은 아니며, 마지막 합격 게이트에서 전체를 BLOCK 처리합니다.
