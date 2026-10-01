# 실습 4 · 멀티컨테이너 (직접 작성)

제공되는 것은 **데이터 파일 하나뿐**입니다. 나머지는 교안을 보고 직접 만듭니다.

```
docker_lab4/
├── data/
│   └── sales.csv          ← 제공 (수정하지 않음)
├── out/                   ← 직접 만든다 (두 컨테이너가 공유할 폴더)
├── report/                ← 직접 만든다
│   ├── requirements.txt
│   ├── report.py
│   └── Dockerfile
├── web/                   ← 직접 만든다
│   └── index.html
└── docker-compose.yml     ← 직접 만든다
```

## 만들 것

| 서비스 | 하는 일 | 바탕 이미지 |
|---|---|---|
| report | pandas로 CSV를 읽어 `report.html`을 만들고 종료 | python:3.12-slim |
| web | `out` 폴더를 웹으로 보여 준다 | nginx:alpine |

두 컨테이너는 **out 폴더를 함께 봅니다.** report가 만든 파일을 web이 보여 주는 구조입니다.

## 완성 후

```
docker compose up --build
브라우저 → http://localhost:8080
```
