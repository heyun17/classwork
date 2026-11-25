# 사전 자료 3. 참고 링크: 누가, 언제, 무엇을 읽나

> 링크를 전부 읽을 필요는 없습니다.
> **실습 전에는 표의 '지금 읽기'만** 읽으면 됩니다 (역할별 2개 + 공통 1개, 약 30분). 나머지는 **실습 중에 막혔을 때** 찾아보는 용도입니다.
> 영어 문서는 처음부터 다 읽지 말고, **첫 문단과 예제 코드**만 먼저 보세요.

## 0. 한눈에 보기

| 언제 | 🔍 기록 담당 | 📘 문서 담당 | 둘이 함께 |
|---|---|---|---|
| **지금 읽기** (실습 전, 혼자) | ① OpenSearch 필드 타입<br>② 정확히 일치하는 검색 | ① Unstructured 파싱 전략<br>② 청킹 | LangGraph 사람 승인(interrupt) |
| 1일차 개인 작업 중 | LangChain 도구 만들기 | OpenSearch 하이브리드 검색 | |
| 1~2일차 그래프 (짝) | | | LangGraph 상태 저장, Postgres 연결 |
| 1~3일차 인프라 (짝) | | | 쿠버네티스 문제 찾기, 프로브, k3s, StatefulSet, Job |
| 3일차 회고 (짝) | | | 사후 회고 문화 |
| 01 문서 6장 조사 | Sysmon, LOLBAS | MITRE ATT&CK, 사고 대응 절차 | |

---

## 1. 🔍 기록 담당이 읽을 것

기록 담당은 **기록을 저장하는 방식**(필드 타입)과 **조건이 정확한 검색**(term, range)을 다룹니다. 01b에서 본 "조사 도구"가 이 두 가지로 만들어집니다.

| | 링크 | 언제 | 읽고 나서 답할 수 있어야 할 것 |
|---|---|---|---|
| ⭐ 지금 | [OpenSearch: Mappings](https://docs.opensearch.org/latest/mappings/)와 [Keyword 타입](https://docs.opensearch.org/latest/mappings/supported-field-types/keyword/) | 실습 전 | 호스트 이름(`WS-007`)은 `text`와 `keyword` 중 무엇으로 저장해야 할까? 왜? |
| ⭐ 지금 | [OpenSearch: Term-level queries](https://docs.opensearch.org/latest/query-dsl/term/index/) | 실습 전 | "WS-007에서 09:00~09:30 사이에 일어난 일"을 찾으려면 어떤 검색 두 가지를 섞어야 할까? |
| 실습 중 | [LangChain: Tools](https://docs.langchain.com/oss/python/langchain/tools) | 1일차 조사 도구 만들 때 | 도구의 설명(docstring)은 왜 중요한가? (LLM이 이 설명을 보고 어떤 도구를 부를지 고릅니다) |

## 2. 📘 문서 담당이 읽을 것

문서 담당은 **PDF를 글자로 바꾸는 방식**(파싱, 청킹)과 **의미로 찾는 검색**(하이브리드)을 다룹니다. 02 문서 9-2에서 열어 본 PDF들이 왜 망가지는지가 여기서 풀립니다.

| | 링크 | 언제 | 읽고 나서 답할 수 있어야 할 것 |
|---|---|---|---|
| ⭐ 지금 | [Unstructured: Partitioning strategies](https://docs.unstructured.io/open-source/concepts/partitioning-strategies) | 실습 전 | 06번 스캔본 PDF에는 `fast`, `hi_res`, `ocr_only` 중 무엇을 써야 할까? 대신 무엇을 포기하나? |
| ⭐ 지금 | [Unstructured: Chunking](https://docs.unstructured.io/open-source/core-functionality/chunking) | 실습 전 | `max_characters`와 `new_after_n_chars`는 어떻게 다른가? |
| 실습 중 | [OpenSearch: Hybrid search](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/) | 1일차 검색 만들 때 | 키워드 검색만으로는 08번 영어 문서를 왜 못 찾을까? |
| 실습 중 | [Unstructured: Partition 함수 목록](https://unstructured.readthedocs.io/en/latest/core/partition.html) | 막혔을 때 | 파일 형식별로 무엇을 지원하나 |

> 실습 기본은 **키워드 검색과 벡터 검색을 따로 하고, 파이썬에서 두 결과를 합치는 방식**입니다. 원리가 눈에 보이기 때문이에요. OpenSearch 내장 하이브리드 기능은 3일차 고도화에서 비교해 봅니다.

## 3. 둘이 함께 읽을 것: LangGraph (그래프는 짝 작업)

두 사람의 도구를 연결하는 에이전트는 둘이 함께 만듭니다. 01b의 **"경비원의 수첩"(Postgres)**이 여기서 나옵니다.

| | 링크 | 언제 | 읽고 나서 답할 수 있어야 할 것 |
|---|---|---|---|
| ⭐ 지금 | [LangGraph: Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | 실습 전 (둘 다) | 그래프가 사람 승인을 기다리며 멈춰 있는 동안, 진행 상황은 어디에 저장될까? |
| 실습 중 | [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | 1일차 오후 그래프 설계 | `thread_id`는 무엇을 구분하는 번호인가? |
| 실습 중 | [PostgresSaver](https://reference.langchain.com/python/langgraph.checkpoint.postgres/PostgresSaver) | 2일차 승인 기능 | `setup()`은 왜 한 번 실행해야 하나? |

**미리 알아 둘 점 두 가지**
- 그래프가 사람 승인에서 멈추면 상태를 저장하고, 누군가 재개할 때까지 **무기한 기다립니다.** 그래서 상태를 저장할 곳(체크포인터)이 꼭 필요해요.
- 재개하면 멈췄던 노드가 **처음부터 다시 실행**됩니다. 그래서 멈추는 지점 앞에 "한 번만 해야 하는 일"(DB에 쓰기 등)을 두면 안 됩니다.

## 4. 둘이 함께 읽을 것: 인프라와 트러블슈팅

인프라는 1일차(0단계, 내 PC)부터 3일차까지 짝과 함께, 단계마다 키보드를 번갈아 잡으며 진행합니다. **지금은 읽지 않아도 됩니다.** 해당 단계에서 막히면 찾아보세요.

| 링크 | 언제 (인프라 단계) |
|---|---|
| [Kubernetes: Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/) | 모든 단계의 '깨 보기' |
| [Kubernetes: Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/) | 파드가 안 뜰 때 (Pending, CrashLoopBackOff) |
| [k3s: Quick-Start](https://docs.k3s.io/quick-start) | 1단계: 서버에 k3s 설치 |
| [Kubernetes: StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) | 2·3단계: OpenSearch, Postgres |
| [Kubernetes: Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) | 4단계: 워커와 API의 상태 확인 |
| [Kubernetes: Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) | 6단계: PDF 적재 작업 |
| [Google SRE Book 12장: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) | 02 문서를 더 깊이 알고 싶을 때 |
| [Google SRE Book 15장: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) | 3일차 사후 회고 쓸 때 |

## 5. 01 문서 6장 조사용 (보안)

01 문서 6장에서 각자 맡은 질문을 조사할 때 출발점으로 씁니다.

| 역할 | 링크 |
|---|---|
| 🔍 기록 담당 | [Microsoft Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) "Event ID 1: Process creation" 부분 · [LOLBAS Project](https://lolbas-project.github.io/) |
| 📘 문서 담당 | [MITRE ATT&CK](https://attack.mitre.org/)에서 T1003.001 검색 · 웹 검색어(구글 등): `NIST SP 800-61`, `incident response playbook` |

---

## 6. 이 문서로 할 일

### 👤 혼자 (실습 전, 약 30분)
1. 0장 표에서 **내 역할의 '지금 읽기' 2개**와 **공통 1개**(LangGraph Interrupts)를 읽습니다.
2. 링크마다 표의 **"읽고 나서 답할 수 있어야 할 것"**에 한두 줄로 답을 적어 봅니다. 정답이 아니어도 됩니다.
3. 마지막에 한 줄을 더 적습니다: **"실습에서 나는 이걸 어디에 쓰게 될까?"**

### 👥 짝과 함께 (1일차 시작, 5분)
1. 서로의 메모를 1분씩 소개합니다. 상대는 내 역할의 링크를 읽지 않았으니, **처음 듣는 사람도 알아듣게** 설명하세요.
2. 둘이 함께 읽은 **LangGraph Interrupts**의 질문("멈춰 있는 동안 진행 상황은 어디에 저장될까?")에 한 문장으로 답을 맞춰 봅니다.
   → 이 답이 01b의 "경비원의 수첩(Postgres)"과 같은 이야기라는 걸 확인하면 됩니다.
