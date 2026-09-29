# Incident Cases

## 문서 목적

이 문서는 Packet.AI 프로젝트에서 Network SRE가 의도적으로 주입한 장애 시나리오와 실제 원인(Ground Truth)을 기록한다.

다른 조원은 장애 원인을 미리 전달받지 않고 패킷과 증상을 바탕으로 원인 후보를 좁히며, 이후 AI 진단 결과와 이 문서의 실제 원인을 비교한다.

> 이 문서에는 장애의 실제 원인과 설정 변경 내용을 기록한다.  
> 복구 과정과 복구 전·후 검증 결과는 `recovery_log.md`에 별도로 기록한다.

---

## Fault 01 — PC3 Default Gateway 오설정

### 1. 장애 시나리오

PC3의 Default Gateway를 정상값이 아닌 주소로 변경하여, PC3가 다른 네트워크로 응답을 돌려보내지 못하도록 구성했다.

### 2. 설정 변경

| 항목 | 정상 상태 | 장애 상태 |
|---|---|---|
| 대상 장비 | PC3 | PC3 |
| PC3 IPv4 | `192.168.20.10` | `192.168.20.10` |
| Default Gateway | `192.168.20.1` | `192.168.20.254` |

### 3. 관찰된 증상

- PC1에서 PC3로 ICMP Echo Request를 전송했다.
- 요청 패킷은 Switch0 → Router0 → Switch0을 거쳐 PC3까지 정상 도착했다.
- PC3는 응답 과정에서 `192.168.20.254`의 MAC 주소를 찾기 위해 ARP Request를 발생시켰다.
- `192.168.20.254`에 대한 ARP Reply가 관찰되지 않았다.
- PC3는 ICMP Echo Reply를 PC1으로 반환하지 못했고 최종 ping은 실패했다.

### 4. 패킷 증거

```text
PC1 → PC3 ICMP Echo Request
        ↓
PC3까지 정상 도착
        ↓
PC3가 응답 경로의 MAC 주소 확인
        ↓
ARP Request
Source IP : 192.168.20.10
Target IP : 192.168.20.254
        ↓
ARP Reply 없음
        ↓
ICMP Echo Reply 전송 불가
        ↓
Ping Failed
```

### 5. Ground Truth

**실제 원인은 PC3의 Default Gateway 오설정이다.**

PC3의 정상 Gateway는 `192.168.20.1`이지만 장애 상태에서는 `192.168.20.254`로 설정되어 있었다. 이 때문에 PC3가 존재하지 않는 Gateway 주소의 MAC을 ARP로 계속 찾았고, 응답 경로를 구성하지 못했다.

### 6. 복구 기준값

```text
PC3 Default Gateway = 192.168.20.1
```

---

## Fault 02 — PC3 연결 포트의 VLAN 오설정

### 1. 장애 시나리오

PC3가 연결된 Switch0의 Access Port를 원래 VLAN 20에서 VLAN 10으로 변경하여, PC3가 자신이 속해야 할 VLAN 20의 ARP Broadcast를 수신하지 못하도록 구성했다.

### 2. 설정 변경

| 항목 | 정상 상태 | 장애 상태 |
|---|---|---|
| 대상 장비 | Switch0 | Switch0 |
| PC3 연결 포트 | `Fa0/3` | `Fa0/3` |
| Access VLAN | VLAN 20 | VLAN 10 |
| PC3 IPv4 | `192.168.20.10` | `192.168.20.10` |

### 3. 관찰된 증상

- PC1에서 PC3로 ICMP Echo Request를 전송했다.
- 요청은 Switch0을 거쳐 Router0까지 정상 도착했다.
- Router0는 목적지 `192.168.20.10`의 MAC 주소를 찾기 위해 ARP Request를 발생시켰다.
- Switch0는 이 ARP Broadcast를 VLAN 20에 속한 포트로 전달했다.
- 그러나 PC3의 연결 포트 `Fa0/3`은 장애 상태에서 VLAN 10에 속해 있어 해당 ARP Request를 수신하지 못했다.
- 따라서 PC3의 ARP Reply가 발생하지 않았고, Router0의 ARP Table에서 `192.168.20.10`은 `Incomplete` 상태로 남았다.
- PC1 → PC3 ping은 최종 실패했다.

### 4. 패킷 증거

```text
PC1 → PC3 ICMP Echo Request
        ↓
Router0까지 정상 도착
        ↓
Router0:
"192.168.20.10의 MAC 주소가 무엇인가?"
        ↓
VLAN 20 ARP Broadcast
        ↓
Switch0는 VLAN 20 포트에만 전달
        ↓
PC3의 Fa0/3은 VLAN 10으로 잘못 설정됨
        ↓
PC3가 ARP Request를 수신하지 못함
        ↓
ARP Reply 없음
        ↓
Router0 ARP Table: 192.168.20.10 = Incomplete
        ↓
Ping Failed
```

### 5. Ground Truth

**실제 원인은 PC3가 연결된 Switch0 `Fa0/3` 포트의 Access VLAN 오설정이다.**

PC3는 `192.168.20.10`을 사용하는 VLAN 20 호스트지만, 스위치 포트가 VLAN 10으로 변경되어 있었다. 따라서 Router0가 VLAN 20에서 발생시킨 ARP Broadcast가 PC3까지 전달되지 않았다.

### 6. 복구 기준값

```text
Switch0 Fa0/3 Access VLAN = VLAN 20
```

---

## Fault 03 — PC1 IPv4 주소 오설정

### 1. 장애 시나리오

PC1의 IPv4 주소를 정상 주소인 `192.168.10.10`에서 `192.168.10.30`으로 변경했다. PC2는 기존 정상 주소 `192.168.10.10`으로 통신을 시도하도록 하여, 해당 IP를 사용하는 장비가 없는 상태를 만들었다.

### 2. 설정 변경

| 항목 | 정상 상태 | 장애 상태 |
|---|---|---|
| 대상 장비 | PC1 | PC1 |
| VLAN | VLAN 10 | VLAN 10 |
| IPv4 주소 | `192.168.10.10` | `192.168.10.30` |

### 3. 테스트 조건

Packet Tracer의 Add Simple PDU로 PC1 아이콘을 직접 선택하면 변경된 현재 주소인 `192.168.10.30`을 대상으로 통신할 수 있으므로, 장애 재현에서는 PC2의 Command Prompt에서 다음 주소로 직접 ping을 수행했다.

```text
ping 192.168.10.10
```

### 4. 관찰된 증상

- PC2는 `192.168.10.10`으로 ping을 시도했다.
- 같은 VLAN의 목적지이므로 PC2는 라우터를 거치기 전에 목적지 MAC 주소를 직접 확인하려 했다.
- PC2가 `192.168.10.10`을 Target IP로 하는 ARP Request를 발생시켰다.
- Switch0는 ARP Request를 VLAN 10에 Broadcast했다.
- PC1의 실제 주소가 `192.168.10.30`으로 변경되어 있었기 때문에 `192.168.10.10`에 대한 ARP Reply를 보내는 장비가 없었다.
- 목적지 MAC 주소를 확인하지 못해 실제 ICMP Echo Request는 PC2 밖으로 전송되지 못했다.
- ARP가 재시도되었지만 응답이 없었고 ping은 실패했다.

### 5. 패킷 증거

```text
PC2:
"192.168.10.10으로 ping을 보내야 한다"
        ↓
목적지 MAC 주소가 없음
        ↓
ARP Request
Target IP : 192.168.10.10
        ↓
Switch0가 VLAN 10에 Broadcast
        ↓
PC1 실제 IP : 192.168.10.30
        ↓
192.168.10.10을 사용하는 장비 없음
        ↓
ARP Reply 없음
        ↓
목적지 MAC 학습 실패
        ↓
ICMP Echo Request를 실제 네트워크로 전송하지 못함
        ↓
Ping Failed
```

### 6. Ground Truth

**실제 원인은 PC1의 IPv4 주소 오설정이다.**

PC1의 정상 주소는 `192.168.10.10`이지만 장애 상태에서는 `192.168.10.30`으로 변경되어 있었다. 따라서 PC2가 정상 주소인 `192.168.10.10`의 MAC 주소를 ARP로 질의해도 응답할 장비가 없었다.

### 7. 복구 기준값

```text
PC1 IPv4 = 192.168.10.10
```

---

## 장애 시나리오 요약

| Case | 장애 유형 | 실제 변경 | 패킷에서 확인된 실패 지점 | Ground Truth |
|---|---|---|---|---|
| Fault 01 | Default Gateway 오류 | PC3 Gateway `192.168.20.1` → `192.168.20.254` | PC3의 `192.168.20.254` ARP 해석 실패 | PC3 Default Gateway 오설정 |
| Fault 02 | Access VLAN 오류 | Switch0 `Fa0/3` VLAN 20 → VLAN 10 | Router0의 `192.168.20.10` ARP 해석 실패 / ARP Table `Incomplete` | PC3 연결 포트 VLAN 오설정 |
| Fault 03 | Host IPv4 오류 | PC1 `192.168.10.10` → `192.168.10.30` | PC2의 `192.168.10.10` ARP 해석 실패 | PC1 IPv4 주소 오설정 |

---

## 다음 단계

이 문서의 Ground Truth를 기준으로 `diagnosis.json`의 AI 원인 후보와 실제 원인을 비교한다. 이후 각 장애를 정상 설정으로 복구하고 동일한 테스트를 다시 수행하여 복구 전·후 결과를 `recovery_log.md`에 기록한다.
