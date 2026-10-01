# 실습 5 · 장애 대응과 K3s (리눅스 VM)

```
docker_lab5/
├── app/                  작은 웹 앱 (/kill 로 일부러 죽일 수 있다)
│   ├── Dockerfile
│   └── app.py
├── docker-compose.yml    restart · healthcheck 비교용
└── k8s/
    ├── deployment.yaml   파드 2개를 유지
    └── service.yaml      NodePort 30080
```

## 1부 · compose로 장애 실습
```bash
docker compose up -d --build
curl localhost:8001 ; curl localhost:8002
curl localhost:8001/kill        # 재시작 안 함
curl localhost:8002/kill        # 자동 재시작
docker compose ps -a
```

## 2부 · K3s
```bash
curl -sfL https://get.k3s.io | sh -
sudo k3s kubectl get nodes
sudo k3s kubectl apply -f k8s/
sudo k3s kubectl get pods -o wide
curl localhost:30080
sudo k3s kubectl delete pod <이름>     # 자동으로 새 파드가 생긴다
```
