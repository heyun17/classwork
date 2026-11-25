# 용량 산정 (16GB 서버 기준)

> 2일차 인프라 2단계를 시작하기 전에 계산합니다. 2단계 운전자(🔍 기록 담당)가 주도하고, 📘 문서 담당이 검토합니다.

| 워크로드 | 종류 | CPU req | Mem req / limit | 힙 | 근거 |
|---|---|---|---|---|---|
| OS + k3s + Traefik | - | | | - | 실측: `free -h`, `kubectl top` |
| opensearch | StatefulSet | | | | |
| postgres | StatefulSet | | | - | |
| api | Deployment | | | - | |
| worker | Deployment | | | - | |
| generator | Deployment | | | - | |
| kb-ingest (일시적) | Job | | | - | |
| **합계 / 여유** | | | | | |
