# Part 01 — 하네스와 Codex 실행·검증 실습

## 실습 파일 안내

- `starter/` : Codex가 완성할 **미구현 시작 코드**. 테스트는 의도적으로 실패한다.
- `reference_solution/` : 작업 뒤 비교할 **정답 예제**. 처음부터 Codex에게 제공하지 않는다.
- `contracts/AGENTS.md` : 하네스 적용 실험에 사용하는 프로젝트 지침.
- `demo/simulate_accident.py` : 임시 폴더에서만 원본 훼손 실패를 재현한다. 제공 원본은 변경하지 않는다.
- `prepare_experiments.py` : `experiments/without_harness`, `experiments/with_harness` 생성.
- `verify_workspace.py` : 실험 폴더 밖에서 독립 채점. 샘플 테스트 파일 수정에 의존하지 않는다.
- `service_guard.py` : 서비스 응답 자체를 검증하는 후속 원리 실습.
- `PROMPTS.md` : 두 실험에 동일하게 전달할 Codex 작업 요청.

## 순서 (Windows PowerShell)

1. ZIP 압축 해제 후 프로젝트 폴더로 이동한다.
2. `python demo/simulate_accident.py` — 임시 복사본만 손상되는 사고 확인.
3. `python prepare_experiments.py` — 하네스 미적용/적용 작업 폴더 준비.
4. `cd experiments/without_harness` → `python -m unittest -v` (실패가 정상) → `codex` → `PROMPTS.md`의 동일한 요청 전달.
5. 루트로 돌아와 `cd experiments/with_harness` → 동일 명령과 동일 요청. 이 폴더에만 `AGENTS.md`가 존재.
6. 루트에서 `python verify_workspace.py experiments/without_harness` 와 `python verify_workspace.py experiments/with_harness` 비교.
7. 참고 검증: `cd reference_solution` → `python -m unittest -v` (5개 통과).
8. 루트에서 `python service_guard.py` — 존재하지 않는 주문 ID·오류 금액 차단.

> Codex 실행 및 기능 변경은 사용자 PC에서 직접 수행하는 실습이다. ZIP에는 Codex 실행 로그/결과가 포함되지 않는다.
> 실제 A/B 실행 결과는 모델·세션에 따라 달라지므로 사전에 특정 승자를 단정하지 않는다.
