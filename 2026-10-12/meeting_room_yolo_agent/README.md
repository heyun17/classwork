# Meeting Room YOLO Agent

회의실 이미지에서 YOLOv8로 사람과 객체를 탐지하고,
OpenAI Agent가 Tool을 선택해 결과를 설명하는 학습용 하네스 프로젝트입니다.

## 구조

- `YOLO`: 사람 수와 객체 탐지
- `Python 규칙`: 비어있음 / 소규모 / 혼잡 상태 판정
- `validator.py`: 결과 검증
- `memory.py`: 분석 이력 저장
- `OpenAI Responses API`: Tool 선택과 자연어 결과 설명
- `AGENTS.md`: Agent 규칙 및 Guardrail
- `MAX_AGENT_STEPS`: 무한 Tool 호출 방지

## 1. 설치

```powershell
python -m pip install -r requirements.txt
```

## 2. API Key 설정

`.env` 파일의 아래 값을 실제 키로 바꿉니다.

```text
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
```

`.env`는 Git에 올리지 않습니다.

## 3. 이미지 넣기

`meeting_rooms/` 폴더에 `.jpg`, `.jpeg`, `.png`, `.webp` 이미지를 넣습니다.

예:

```text
meeting_rooms/
├─ meeting1.jpg
├─ meeting2.jpg
└─ meeting3.jpg
```

## 4. 실행

```powershell
python main.py
```

요청 예:

```text
현재 회의실 전체 상태를 분석하고 비어 있는 회의실을 알려줘.
```

## 5. 결과

- Bounding Box가 그려진 이미지는 `outputs/`에 저장됩니다.
- 검증을 통과한 분석 기록은 `data/history.jsonl`에 저장됩니다.

## 상태 기준

- 0명: 🟢 비어있음
- 1~4명: 🟡 소규모
- 5명 이상: 🔴 혼잡

## 주의

기본 `yolov8n.pt`는 COCO 사전학습 모델입니다.
사람 수는 YOLO의 `person` 탐지 결과를 사용합니다.

Agent가 사람 수를 추측하지 않도록 설계되어 있습니다.
