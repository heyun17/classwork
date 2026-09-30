# 도커 실습 · 두 개의 이미지와 포트 통신

```
docker_lab2/
├── api/            # ① 매출 집계 API (파이썬)
│   ├── Dockerfile
│   ├── api.py
│   └── sales.csv
└── site/           # ② 대시보드 화면 (nginx)
    ├── Dockerfile
    ├── index.html
    └── style.css
```

## 실습 순서 (Windows PowerShell · VS Code 터미널)

```powershell
# ① API 이미지
cd api
docker build -t my-api:1.0 .
docker run -d -p 5000:5000 --name api my-api:1.0
curl http://localhost:5000/api/summary

# ② 사이트 이미지
cd ..\site
docker build -t my-site:1.0 .
docker run -d -p 8080:80 --name site my-site:1.0

# 브라우저에서 http://localhost:8080
```

## 컨테이너끼리 직접 통신 (같은 네트워크)

```powershell
docker network create labnet
docker rm -f api site
docker run -d --network labnet -p 5000:5000 --name api  my-api:1.0
docker run -d --network labnet -p 8080:80   --name site my-site:1.0
docker exec site wget -qO- http://api:5000/api/health
```

## VM으로 옮기기

```powershell
docker save -o my-api.tar my-api:1.0
docker save -o my-site.tar my-site:1.0
multipass transfer my-api.tar my-site.tar myUbuntu1:/home/ubuntu/
```
```bash
# VM 안에서
docker load -i my-api.tar
docker load -i my-site.tar
docker run -d -p 5000:5000 --name api  my-api:1.0
docker run -d -p 8080:80   --name site my-site:1.0
```
