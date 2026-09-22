# GitHub 3인 협업 방법

## 1. 한 명이 저장소 생성
```bash
git init -b main
git add .
git commit -m "init chatbot efficiency monitor"
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
```

## 2. 나머지 두 명은 clone
```bash
git clone <GITHUB_REPOSITORY_URL>
cd chatbot-efficiency-monitor
```

## 3. 각자 브랜치 생성
담당 A:
```bash
git switch -c feature/data-db
```

담당 B:
```bash
git switch -c feature/analysis
```

담당 C:
```bash
git switch -c feature/dashboard-docs
```

## 4. 작업 후 push
```bash
git status
git add .
git commit -m "feat: add analysis metrics"
git push -u origin feature/analysis
```

## 5. GitHub에서 Pull Request
- feature 브랜치 → main PR 생성
- 다른 팀원 1명이 코드 확인
- CI 성공 확인
- main에 Merge

## 6. 다른 사람이 merge한 뒤 내 작업 시작 전
```bash
git switch main
git pull origin main
git switch feature/analysis
git merge main
```

## 충돌 최소화 규칙
- A는 `data/`, `database/`, `scripts/build_db.py` 중심
- B는 `analysis/`, `tests/` 중심
- C는 `app.py`, `docs/`, `README.md` 중심
- 공용 파일 `requirements.txt`, `TASK.md` 변경 전에는 단체 채팅에 알린다.

## ChatGPT / Codex 사용
- ChatGPT: 설계, 설명, 오류 원인 분석, 코드 리뷰, 발표 문서에 사용.
- Codex: 실제 저장소에서 반복 수정이 필요한 경우에만 최소 사용.
- Codex 요청은 파일과 범위를 제한한다. 예: `analysis/metrics.py의 함수만 수정. app.py와 data는 수정 금지.`
- AI가 만든 코드는 바로 main에 넣지 말고 테스트/PR을 거친다.
