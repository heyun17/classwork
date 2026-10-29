# LLMOps 따라하기 — 쇼핑몰 FAQ 챗봇

FAQ·동의어 사전·평가셋 파일이 바뀌면 **검증 → 정제·재색인 → 회귀 평가 → 게이트 → 활성 버전 교체**가
자동으로 일어나는 LLMOps 실습입니다. (서버 배포는 제외)

## 1. 환경 만들기
```
cd llmops-faq
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS · Linux
pip install kiwipiepy scikit-learn transformers torch openai python-dotenv ipykernel
```
GPT를 쓰려면 이 폴더에 `.env` 파일을 만들고 `OPENAI_API_KEY=sk-...`를 적습니다. 없으면 mock 답변으로 끝까지 실행됩니다.

## 2. 실행 순서
1. `01_따라하기.ipynb` — 위에서부터 실행 (구현 → Day 0~3 시나리오)
2. `python watch.py` — 터미널에 켜 두고 `data/faq.csv`를 고쳐 저장하면 파이프라인이 저절로 돕니다
3. `02_실습과제.ipynb` — 과제 9개 (정답: `02_실습과제_정답.ipynb`)

## 3. 파일
| 파일 | 설명 |
|---|---|
| `llmops_core.py` | 01 노트북 코드를 모은 파일. watch.py와 실습 과제가 불러다 씀 |
| `watch.py` | 5초마다 변경 감지 → 파이프라인 자동 실행 |
| `data/` | 사람이 고치는 곳: faq.csv · synonyms.csv · eval_set.jsonl (첫 실행 때 생성) |
| `artifacts/` | 버전별 색인과 평가 결과 (자동 생성) |
| `registry.json` | 활성 버전 · 이력 (자동 생성) |
| `logs/` | 파이프라인 실행 · 서빙 로그 · 피드백 · 검토 큐 (자동 생성) |

처음 상태로 되돌리려면 노트북에서 `init_project(reset=True)`를 실행합니다.
