# Network Recovery Agent
### 네트워크 연결을 자동으로 재시작하고 정상 복구 여부까지 확인하는 관리 에이전트

---

## PROJECT MISSION

**네트워크 연결에 일시적인 문제가 발생했을 때 관리자가 반복적으로 수행하는  
「연결 해제 → 대기 → 재연결 → 상태 확인」 작업을 하나의 에이전트로 자동화한다.**

사용자가 직접 네트워크 설정 화면을 열거나 여러 명령을 입력하지 않아도  
에이전트가 정해진 순서에 따라 작업을 수행하고 최종 결과를 보고한다.

---

## 사용할 에이전트

### Network Recovery Agent

**역할**  
Windows PC의 현재 네트워크 상태를 확인하고, 활성 네트워크 어댑터를 일시적으로 재시작한 뒤 인터넷 연결이 정상적으로 복구되었는지 확인하는 시스템 관리 에이전트.

**주요 기능**

| 기능 | 에이전트의 작업 |
|---|---|
| Adapter Detection | 현재 활성화된 Wi-Fi / Ethernet 어댑터 확인 |
| Disconnect | 해당 네트워크 어댑터 비활성화 |
| Recovery Wait | 10초 동안 대기 |
| Reconnect | 네트워크 어댑터 다시 활성화 |
| Connection Test | `ping`을 이용해 외부 통신 확인 |
| Result Report | 성공 또는 실패 상태를 사용자에게 보고 |

---

## AUTOMATION FLOW

**① Detect**  
Active Network Adapter 확인

**→ ② Disconnect**  
`Disable-NetAdapter`

**→ ③ Wait**  
10 Seconds

**→ ④ Reconnect**  
`Enable-NetAdapter`

**→ ⑤ Verify**  
`Test-Connection 8.8.8.8`

**→ ⑥ Report**  
`SUCCESS / FAILED`

---

## 에이전트가 판단하는 범위

Network Recovery Agent는 **네트워크 복구에 필요한 최소 작업만 수행한다.**

- 활성 네트워크 어댑터 확인
- 네트워크 연결 재시작
- 인터넷 연결 여부 검사
- 작업 중 오류 발생 위치 확인
- 최종 작업 결과 보고

에이전트는 문제가 발생했다고 해서 임의로 다른 시스템 설정을 변경하지 않는다.

---

## SAFETY RULE

**다음 작업은 수행하지 않는다.**

IP 주소 변경 · DNS 변경 · Gateway 변경 · 드라이버 설치 · 프로그램 설치 ·  
방화벽 변경 · Windows 설정 변경 · 다른 네트워크 어댑터 임의 조작

관리자 권한 부족 또는 명령 실행 오류가 발생하면  
**작업을 중단하고 오류 내용을 보고한다.**

---

## SUCCESS CONDITION

다음 조건을 만족하면 작업을 완료한 것으로 판단한다.

**Network Adapter = Enabled**  
**Ping Test = Success**  
**Final Status = Network connection is working**

---

### 한 줄 정의

> **Network Recovery Agent = 네트워크를 재시작하는 것에서 끝나지 않고, 실제 연결 복구 여부까지 확인해서 보고하는 자동화 에이전트**