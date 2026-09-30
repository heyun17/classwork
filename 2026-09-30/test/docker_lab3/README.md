# 도커 실습 3 · docker compose

```
docker_lab3/
├── docker-compose.yml   # 두 서비스를 한 파일로
├── data/
│   └── sales.csv        # 이미지 밖의 데이터 (볼륨으로 붙인다)
├── api/
│   ├── Dockerfile
│   └── api.py
└── site/
    ├── Dockerfile
    ├── index.html
    └── style.css
```

## 기본 사용

```powershell
docker compose up -d --build     # 굽고 띄우기
docker compose ps                # 상태
docker compose logs -f api       # 로그
docker compose exec api sh       # 컨테이너 안으로
docker compose down              # 멈추고 지우기
```

브라우저 : http://localhost:8080
API 확인 : http://localhost:5000/api/summary
