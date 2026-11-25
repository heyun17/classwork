# 인프라 단계별 가이드: 직접 쓰고, 깨 보고, 고친다 (0~7단계)

> 정답 매니페스트는 없습니다. **요구사항을 보고 직접 작성**합니다. 막히면 [`03 문서`](../prep/03_references.md) 4장의 링크와 공식 문서를 찾으세요.
> 매니페스트는 `infra/` 아래에 단계마다 추가하고, **단계마다 커밋**하세요 (`git log`가 성장 기록이 됩니다).

## 모든 단계의 공통 구조

| 칸 | 내용 |
|---|---|
| **왜** | 이 단계가 필요한 이유. 만들기 전에 짝과 짧게 이야기해 봅니다 |
| **만들 것** | 요구사항. YAML은 직접 작성 |
| **성공 확인** | 이 명령의 결과가 이렇게 보이면 통과 |
| **🔥 깨 보기** | 출제자가 목록에서 하나를 골라 몰래 넣고, 진단자가 찾는다. 찾은 뒤 둘이 **진단 후 나눔**을 한다 (아래 깨 보기 규칙). 복구까지 걸린 시간을 기록한다 |
| **기록** | `docs/RUNBOOK.md`에 02 문서 8장의 '좋은 런북' 형식으로: 증상 → 확인 명령과 출력 → 원인 → 조치 → 재발 방지 |

## 단계별 운전자

운전자가 키보드를 잡고 만들고, **깨 보기에서는 운전자가 진단자, 다른 한 명이 출제자**입니다.
자기 역할과 가까운 단계는 그 역할이 운전하고, 나머지는 번갈아 맡습니다.

| 단계 | 일차 | 운전 (진단자) | 출제자 | 이 역할이 운전하는 이유 |
|---|---|---|---|---|
| 0. 내 PC에서 전부 띄우기 | 1 | 🔍 기록 담당 | 📘 | OpenSearch를 먼저 다뤄 봄 |
| 1. 서버 준비 + 첫 Deployment | 2 | 📘 문서 담당 | 🔍 | 번갈아 |
| 2. OpenSearch (StatefulSet) | 2 | 🔍 기록 담당 | 📘 | 기록이 쌓이는 곳, 인덱스와 용량을 직접 다룸 |
| 3. Postgres + Secret + ConfigMap | 2 | 📘 문서 담당 | 🔍 | 번갈아 |
| 4. 워커 + 생성기 + 프로브 | 2 | 🔍 기록 담당 | 📘 | 생성기가 기록을 만들어 넣는 단계 |
| 5. Ingress (외부 공개) | 2 | 📘 문서 담당 | 🔍 | 번갈아 |
| 6. 일회성 작업은 Job으로 | 3 | 📘 문서 담당 | 🔍 | PDF 적재 파이프라인을 서버에서 실행 |
| 7. CI → 배포 → 롤백 | 3 | 🔍 기록 담당 | 📘 | 번갈아 |

## 🔥 깨 보기 규칙 (02 문서 7장)

깨 보기는 **출제 → 진단 → 진단 후 나눔** 세 부분으로 진행합니다. 마지막 '진단 후 나눔'까지 해야 한 문제가 끝납니다.

**출제와 진단**
1. 출제자는 무엇을 깼는지 종이에 적어 뒤집어 둡니다.
2. 진단자는 [`02 문서`](../prep/02_troubleshooting.md) 2장의 순서대로 찾습니다. **관찰 → 가설 → 검증** 과정을 소리 내어 말하면서요. 출제자는 그 말을 들으며 진단자가 어떤 순서로 생각하는지 메모합니다.
3. 출제자는 힌트를 주지 않습니다. 진단자가 충분히 막혔다고 요청하면 힌트를 1개 줍니다.
4. 원인을 찾으면 복구하고, 진단자가 RUNBOOK에 증상, 확인 명령과 출력, 원인, 조치를 적습니다.

**진단 후 나눔 (👥)**

**왜:** 진단자는 자기가 걸어간 길만 압니다. 출제자는 답을 알고 진단 과정을 옆에서 지켜봤기 때문에, **더 빠른 길이 어디 있었는지** 볼 수 있습니다. 두 사람의 시선을 합쳐야 런북의 '재발 방지'와 '처음 확인할 곳'이 진짜로 쓸모 있어집니다. 실무에서 장애가 끝난 뒤 짧게 되돌아보는 것과 같습니다.

5. 세 가지를 차례로 이야기합니다.
   | 누가 | 이야기할 것 | 예 |
   |---|---|---|
   | 진단자 | 가장 오래 걸린 지점과 그 이유 | "파드가 Running이라 앱 문제라고 생각해서 로그만 봤다" |
   | 출제자 | 메모를 보며, 나라면 어디부터 봤을지 | "502였으니 Service 연결부터 봤을 것 같다. `get endpointslices` 한 번이면 끝났다" |
   | 둘이 함께 | 다음에 같은 증상을 보면 **처음 칠 명령 하나** | `kubectl -n soc get endpointslices` |
6. 정한 '처음 칠 명령'과 재발 방지를 RUNBOOK의 해당 칸에 적습니다.
7. 각자 **02 문서 9-2의 고장 예상표**와 비교합니다. 예상한 증상이었나요? 처음 확인할 곳은 맞았나요?

---

## 0단계. 로컬에서 전부 띄우기 (docker compose) · 1일차 · 운전 🔍

**왜:** 서버에 올리기 전에 "내 PC에서는 되는" 기준선이 필요합니다. 서버에서 안 되면 **로컬과 무엇이 다른지**가 첫 단서가 됩니다.

**만들 것:** `docker-compose.yml`
- OpenSearch 단일 노드 (보안 플러그인 끄기, 힙 1GB, 9200 포트, 데이터 볼륨)
- OpenSearch Dashboards (5601)
- Postgres 16 (사용자·DB·비밀번호, 5432, 데이터 볼륨)
- (선택) 앱 컨테이너: `Dockerfile`로 빌드, 환경변수로 OpenSearch·Postgres 주소 지정

**성공 확인**
```bash
curl -s localhost:9200/_cluster/health | jq .status    # "green" 또는 "yellow"
psql postgresql://soc:soc@localhost:5432/soc -c 'select 1'
```

**🔥 깨 보기 (출제 목록)**
| # | 넣는 장애 | 진단자가 찾을 단서 |
|---|---|---|
| 0-1 | 앱 컨테이너의 `OPENSEARCH_URL`을 `http://localhost:9200`으로 | 컨테이너 안의 localhost는 자기 자신 → 서비스 이름으로 접속해야 함 |
| 0-2 | 다른 프로그램이 5432 포트를 이미 쓰게 만들기 | `port is already allocated` |
| 0-3 | (Linux) `vm.max_map_count`를 65530으로 되돌리기 | OpenSearch 로그의 `max virtual memory areas` |

**설명할 수 있어야 할 것:** 볼륨이 없으면 `docker compose down` 후 무슨 일이 생기나?

---

## 1단계. 서버 준비 + 첫 Deployment · 2일차 · 운전 📘

**왜:** 가장 단순한 앱 하나를 먼저 올려 **서버 → k3s → 이미지 → 파드 → 포트포워딩** 경로를 확인합니다. 문제가 생겨도 범위가 좁아요.

**만들 것**
1. 강사가 준 팀 서버(가비아, Ubuntu)에 SSH 키로 접속. `sudo`가 되는지, vCPU와 메모리가 얼마인지 먼저 확인합니다 (`nproc`, `free -h`). 이 숫자가 2단계 `CAPACITY.md`의 출발점입니다.
2. 서버 초기 설정 스크립트 `infra/scripts/bootstrap.sh`를 **직접 작성**:
   - 방화벽: 22, 80, 443 허용. 6443은 **내 IP만** 허용 (왜?)
   - `vm.max_map_count=262144`를 **재부팅 후에도 유지**되게
   - swap 끄기 (왜?)
3. k3s 설치 ([Quick-Start](https://docs.k3s.io/quick-start)). 노트북에서 kubectl을 쓰려면 공인 IP를 인증서에 넣는 옵션이 필요합니다. 찾아보세요.
4. 앱 이미지를 빌드해 레지스트리(GHCR)에 직접 push.
5. `infra/k8s/10-namespace.yaml`, `11-api.yaml`: API **Deployment + Service(ClusterIP)**. 이 단계에서는 `BACKEND=memory` (외부 의존성 없음).

**성공 확인**
```bash
kubectl get nodes                                  # 노트북에서 Ready
kubectl -n soc get pods                            # api-xxxx  1/1 Running
kubectl -n soc port-forward svc/api 8000:80 & curl -s localhost:8000/healthz
```

**🔥 깨 보기**
| # | 넣는 장애 | 단서 |
|---|---|---|
| 1-1 | 이미지 태그 오타 | `ImagePullBackOff`, `describe`의 Events |
| 1-2 | GHCR 패키지를 private으로 두고 pull secret 없이 | `ErrImagePull ... unauthorized` |
| 1-3 | `containerPort`와 Service `targetPort` 불일치 | 파드는 Running인데 port-forward 접속 실패 |
| 1-4 | kubeconfig의 server 주소를 127.0.0.1로 둔 채 노트북에서 | `connection refused` |

**설명할 수 있어야 할 것:** Deployment, ReplicaSet, Pod의 관계. 파드를 지우면 왜 다시 생기나?

---

## 2단계. OpenSearch를 StatefulSet으로 · 2일차 · 운전 🔍

**왜:** OpenSearch는 **데이터를 가진** 워크로드입니다. 파드가 다시 만들어져도 데이터와 이름이 유지돼야 하므로 Deployment가 아니라 StatefulSet + PVC를 씁니다.

**만들 것:** `infra/k8s/20-opensearch.yaml`
- StatefulSet (replicas 1), `volumeClaimTemplates` (k3s 기본 StorageClass `local-path`)
- Service 2개: 앱이 접속할 ClusterIP, StatefulSet용 headless (왜 둘?)
- 리소스: **먼저 `docs/CAPACITY.md`를 계산**하고 requests/limits와 힙 크기(`OPENSEARCH_JAVA_OPTS`)를 정합니다. 규칙: 힙 ≈ 메모리 limit의 50%
- readiness 프로브 (`/_cluster/health?local=true`)

**성공 확인**
```bash
kubectl -n soc get sts,pvc                      # opensearch 1/1, PVC Bound
kubectl -n soc delete pod opensearch-0          # 지웠다가
# 다시 Ready가 된 뒤 이전에 넣은 데이터가 남아 있는가? (_count 비교)
```

**🔥 깨 보기**
| # | 넣는 장애 | 단서 |
|---|---|---|
| 2-1 | 서버에서 `sysctl -w vm.max_map_count=65530` 후 파드 삭제 | `CrashLoopBackOff` + 로그 |
| 2-2 | 힙 2g, 메모리 limit 2Gi | `OOMKilled` (Last State) |
| 2-3 | StorageClass 이름 오타 | PVC `Pending` → 파드 `Pending` |
| 2-4 | requests.memory를 서버 메모리보다 크게 | `Insufficient memory` |
| 2-5 | 인덱스 `number_of_replicas: 1` | 클러스터 상태 `yellow` (왜 노드 1개에서는?) |

**설명할 수 있어야 할 것:** PVC를 지우면? StatefulSet을 지우면 PVC는? 왜 그렇게 설계됐나?

---

## 3단계. Postgres + Secret + ConfigMap · 2일차 · 운전 📘

**왜:** 에이전트가 사람 승인에서 멈췄다가 이어 가려면, 그 상태를 **파드 밖**에 저장해야 합니다(체크포인터). 그리고 비밀번호는 Git이 아니라 클러스터에만 있어야 합니다.

**만들 것:** `infra/k8s/30-postgres.yaml`, `31-config.yaml`
- Postgres StatefulSet + PVC + Service
- **Secret은 YAML로 커밋하지 않습니다.** `kubectl create secret ... --dry-run=client -o yaml | kubectl apply -f -` 명령을 `infra/scripts/secrets.sh`로
  - `OPENAI_API_KEY`, `POSTGRES_PASSWORD`, `POSTGRES_DSN`
- ConfigMap: `BACKEND=real`, `OPENSEARCH_URL`, 모델 이름 등 비밀이 아닌 설정
- API Deployment가 `envFrom`으로 둘 다 받도록 수정

**성공 확인**
```bash
kubectl -n soc exec -it postgres-0 -- psql -U soc -c '\dt'   # 체크포인트 테이블이 생겼는가 (앱 기동 후)
kubectl -n soc logs deploy/api | grep -i postgres
```

**🔥 깨 보기**
| # | 넣는 장애 | 단서 |
|---|---|---|
| 3-1 | Secret 삭제 후 API 파드 재시작 | `CreateContainerConfigError` |
| 3-2 | **Postgres가 이미 초기화된 뒤** Secret의 비밀번호만 변경 | `password authentication failed` (왜? 공식 이미지 문서에서 찾기). 02 문서 9-1에서 명령 결과로 풀어 본 바로 그 장애입니다 |
| 3-3 | DSN의 호스트를 `localhost`로 | 연결 거부 |
| 3-4 | ConfigMap 값을 바꾸고 파드를 재시작하지 않음 | 바뀐 값이 반영 안 됨 (envFrom은 언제 읽히나?) |

**설명할 수 있어야 할 것:** Secret은 정말 '비밀'인가? (base64) 그럼 무엇으로 보호해야 하나?

---

## 4단계. 워커 + 생성기 + 프로브 · 2일차 · 운전 🔍

**왜:** 워커는 **계속 도는(long-running)** 프로세스입니다. 웹 서버와 '건강하다'의 의미가 다릅니다. 프로브를 잘못 설계하면 멀쩡한 파드가 계속 재시작되거나, 고장 난 파드가 계속 트래픽을 받습니다.

**만들 것:** `infra/k8s/40-generator.yaml`, `41-worker.yaml`, API 프로브 추가
- generator Deployment: 시뮬레이터 + 탐지 룰 (이벤트와 알림 생성)
- worker Deployment: `status=new` 알림을 가져가 에이전트 실행. 메트릭·헬스 포트 9100
- **프로브 설계를 먼저 표로** `docs/DECISIONS.md`에 쓰고 구현:

| | API | 워커 |
|---|---|---|
| liveness (실패 → 재시작) | `/healthz`: 프로세스가 살아 있나 | `/healthz`: **하트비트**(루프가 최근에 돌았나) |
| readiness (실패 → 트래픽 제외) | `/readyz`: OpenSearch·Postgres 연결 | 필요한가? 워커는 트래픽을 받지 않는다 |
| 종료 유예 | 기본값 | 처리 중인 알림을 마칠 시간 (`terminationGracePeriodSeconds`) |

**성공 확인**
```bash
kubectl -n soc get pods                          # 모두 1/1, RESTARTS 0
# 알림 수 변화: status=new가 쌓였다가 줄어드는가?
curl -s localhost:9200/edr-alerts/_count -H 'content-type: application/json' -d '{"query":{"term":{"status":"new"}}}'
```

**🔥 깨 보기**
| # | 넣는 장애 | 단서 |
|---|---|---|
| 4-1 | API liveness를 `/readyz`로 + Postgres 중지 | DB가 죽었는데 API가 **재시작 반복** (왜 나쁜가?) |
| 4-2 | 워커 liveness `periodSeconds: 5, failureThreshold: 1` | LLM 응답을 기다리는 동안 재시작 반복 |
| 4-3 | `kubectl scale deploy/worker --replicas=0` | 파드 오류는 없는데 `status=new`가 계속 쌓임 → **파이프라인 어디서 멈췄나** (01b 문서 4장 "워커가 멈춤") |
| 4-4 | 워커에 잘못된 `OPENAI_API_KEY` | 워커 로그의 401, 알림이 실패 상태로 |
| 4-5 | 처리 중에 `kubectl delete pod` 워커 | 새 파드가 같은 알림을 **이어서** 처리하는가? (01b 문서의 "경비원의 수첩" = 체크포인트) |

**설명할 수 있어야 할 것:** 4-1에서 liveness가 DB를 검사하면 왜 장애가 커지나?

---

## 5단계. Ingress로 외부 공개 · 2일차 · 운전 📘

**왜:** 분석가가 승인 API를 쓰고, Dify가 📘 문서 담당의 플레이북 검색을 부르려면 외부에서 접속할 수 있어야 합니다.

**만들 것:** `infra/k8s/50-ingress.yaml`
- k3s 기본 Traefik 사용, 호스트 `soc.<서버IP>.nip.io` (또는 가비아 도메인 A 레코드)
- `/` → api Service

**성공 확인:** 노트북에서 `curl http://soc.<IP>.nip.io/healthz`

**🔥 깨 보기**
| # | 넣는 장애 | 단서 |
|---|---|---|
| 5-1 | Ingress host 오타 | Traefik `404 page not found` |
| 5-2 | Service selector를 `app: apii`로 | `502`, `kubectl get endpointslices`가 비어 있음 |
| 5-3 | 서버 방화벽에서 80 닫기 | 타임아웃 (404·502와 무엇이 다른가) |
| 5-4 | API readiness를 항상 실패하게 | `502`, 파드는 Running 0/1 |

**설명할 수 있어야 할 것:** 404, 502, 504, 타임아웃을 각각 보면 어느 층을 의심하나?

---

## 6단계. 일회성 작업은 Job으로 · 3일차 · 운전 📘

**왜:** 플레이북 적재, 인덱스 초기화는 **한 번 실행하고 끝나는** 작업입니다. 계속 도는 Deployment에 넣으면 끝없이 재시작합니다.

**만들 것:** `infra/k8s/60-setup-job.yaml`, `61-kb-ingest-job.yaml`
- setup Job: 인덱스 템플릿 생성 (여러 번 실행해도 안전하게, 멱등)
- kb-ingest Job: Unstructured 이미지(무거움 → 앱 이미지와 분리), PDF를 이미지에 포함
- `backoffLimit`, `activeDeadlineSeconds`, `ttlSecondsAfterFinished`를 정하고 이유를 기록
- OpenSearch가 준비될 때까지 기다리는 initContainer

**성공 확인:** `kubectl -n soc get jobs` → `Complete`, KB 인덱스 문서 수 확인, RAG 평가 재실행

**🔥 깨 보기**
| # | 넣는 장애 | 단서 |
|---|---|---|
| 6-1 | Job의 `OPENSEARCH_URL` 오타 | `BackoffLimitExceeded`, 시도별 파드 로그 |
| 6-2 | `PARSE_STRATEGY=hi_res` + 메모리 limit 512Mi | `OOMKilled` |
| 6-3 | 이미 완료된 Job의 spec을 바꿔 `apply` | `field is immutable` (Job은 왜 수정이 안 되나) |

---

## 7단계. CI → 배포 → 롤백 · 3일차 · 운전 🔍

**왜:** 손으로 빌드하고 push하면 "지금 서버에 뜬 게 어떤 코드인지" 모르게 됩니다. 롤백하려면 **이미지 태그 = 커밋**이어야 합니다.

**만들 것:** `.github/workflows/ci.yml`
- 테스트 → 이미지 빌드 → GHCR push, 태그 = 커밋 SHA 7자리 (`latest` 금지, 왜?)
- 배포: `kubectl set image` 또는 Kustomize `images:`로 태그 교체
- 롤백: `kubectl rollout undo`, `rollout history`

**성공 확인:** 코드를 바꿔 push → 새 태그로 배포 → `kubectl rollout history`에 기록 → 롤백 성공

**🔥 깨 보기**
| # | 넣는 장애 | 단서 |
|---|---|---|
| 7-1 | 시작 즉시 죽는 이미지를 배포 | 롤링 업데이트가 멈춤, **기존 파드는 계속 서비스** (`maxUnavailable` 설정의 의미) |
| 7-2 | 워크플로에서 `packages: write` 권한 제거 | GHCR push `denied` |
| 7-3 | 저장소 이름에 대문자 | `repository name must be lowercase` |

---

## 마무리: 단계별 체크리스트

| 단계 | 리소스 | 깨 보기 완료 | RUNBOOK 기록 | 커밋 |
|---|---|---|---|---|
| 0 | compose | ☐ | ☐ | ☐ |
| 1 | Deployment, Service | ☐ | ☐ | ☐ |
| 2 | StatefulSet, PVC | ☐ | ☐ | ☐ |
| 3 | Secret, ConfigMap | ☐ | ☐ | ☐ |
| 4 | 프로브, 장기 실행 워커 | ☐ | ☐ | ☐ |
| 5 | Ingress | ☐ | ☐ | ☐ |
| 6 | Job | ☐ | ☐ | ☐ |
| 7 | CI, 롤백 | ☐ | ☐ | ☐ |
