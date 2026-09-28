# Network Specification

## 1. 구성 목적

Packet Tracer에서 소규모 네트워크를 구성하고, VLAN 간 통신이 정상적으로 이루어지는 기준 환경을 만든다.

- PC 3대
- L2 Switch 1대
- Router 1대
- VLAN 10 / VLAN 20 분리
- Router-on-a-Stick 방식으로 VLAN 간 라우팅 구성

---

## 2. Topology

```text
PC1 192.168.10.10/24 ─┐
                       ├─ VLAN 10 ─┐
PC2 192.168.10.20/24 ─┘           │
                                   ├─ Switch0 ── Trunk ── Router0
PC3 192.168.20.10/24 ─── VLAN 20 ──┘
```

### 장비

| 장비 | 모델/종류 | 역할 |
|---|---|---|
| PC1 | PC-PT | VLAN 10 단말 |
| PC2 | PC-PT | VLAN 10 단말 |
| PC3 | PC-PT | VLAN 20 단말 |
| Switch0 | Cisco 2960-24TT | L2 스위치, VLAN 분리 및 Trunk |
| Router0 | Cisco 2911 | VLAN 10 ↔ VLAN 20 라우팅 |

---

## 3. IPv4 / CIDR 설계

| 장비 | IPv4 Address | CIDR | Subnet Mask | Default Gateway |
|---|---|---:|---|---|
| PC1 | 192.168.10.10 | /24 | 255.255.255.0 | 192.168.10.1 |
| PC2 | 192.168.10.20 | /24 | 255.255.255.0 | 192.168.10.1 |
| PC3 | 192.168.20.10 | /24 | 255.255.255.0 | 192.168.20.1 |

### 네트워크

- VLAN 10: `192.168.10.0/24`
- VLAN 20: `192.168.20.0/24`

DNS Server는 이번 실습에서 사용하지 않으므로 `0.0.0.0`으로 유지한다.

---

## 4. VLAN 구성

| VLAN | 연결 장비 | 용도 |
|---|---|---|
| VLAN 10 | PC1, PC2 | 동일 네트워크 그룹 |
| VLAN 20 | PC3 | 별도 네트워크 그룹 |

### Switch 포트 배정

| Switch0 Port | 연결 장비 | 설정 |
|---|---|---|
| FastEthernet0/1 | PC1 | Access / VLAN 10 |
| FastEthernet0/2 | PC2 | Access / VLAN 10 |
| FastEthernet0/3 | PC3 | Access / VLAN 20 |
| GigabitEthernet0/1 | Router0 | Trunk |

---

## 5. Switch0 설정

### VLAN 생성

```text
VLAN 10
VLAN 20
```

### PC 연결 포트

- Fa0/1 → Access VLAN 10
- Fa0/2 → Access VLAN 10
- Fa0/3 → Access VLAN 20

### Router 연결 포트

```cisco
enable
configure terminal

interface gigabitEthernet 0/1
switchport mode trunk
exit

end
```

확인:

```cisco
show interfaces gigabitEthernet 0/1 switchport
show interfaces trunk
```

---

## 6. Router0 설정

Switch0와 Router0는 다음 인터페이스로 연결한다.

```text
Switch0 Gi0/1 ↔ Router0 Gi0/0
```

Router0의 물리 인터페이스를 활성화한다.

```cisco
enable
configure terminal

interface gigabitEthernet 0/0
no shutdown
exit
```

### VLAN 10 Subinterface

```cisco
interface gigabitEthernet 0/0.10
encapsulation dot1Q 10
ip address 192.168.10.1 255.255.255.0
exit
```

### VLAN 20 Subinterface

```cisco
interface gigabitEthernet 0/0.20
encapsulation dot1Q 20
ip address 192.168.20.1 255.255.255.0
exit

end
```

---

## 7. Gateway / Routing 구조

Router0가 각 VLAN의 Default Gateway 역할을 한다.

```text
VLAN 10 → 192.168.10.1
VLAN 20 → 192.168.20.1
```

Router-on-a-Stick 방식으로 하나의 물리 인터페이스 `Gi0/0`에 두 개의 Subinterface를 구성한다.

```text
Router0 Gi0/0
 ├─ Gi0/0.10 → VLAN 10 → 192.168.10.1
 └─ Gi0/0.20 → VLAN 20 → 192.168.20.1
```

---

## 8. 통신 검증

### PC1 → PC2

```text
Source:      192.168.10.10
Destination: 192.168.10.20
Result:      Success
TTL:         128
```

PC1과 PC2는 같은 VLAN 10에 있으므로 Router를 거치지 않고 L2 Switch를 통해 직접 통신한다.

### PC1 → PC3

```text
Source:      192.168.10.10
Destination: 192.168.20.10
Result:      Success
TTL:         127
```

PC1과 PC3는 서로 다른 VLAN에 있으므로 Router0를 1회 거쳐 통신한다.

```text
PC1
 ↓
Switch0 / VLAN 10
 ↓
Router0
 ↓
Switch0 / VLAN 20
 ↓
PC3
```

L2 Switch 통과 자체로는 TTL이 감소하지 않고, L3 라우팅 홉을 지날 때 TTL이 감소한다.

---

## 9. 현재 상태

- Topology 구성 완료
- IPv4/CIDR 설계 완료
- VLAN 10 / VLAN 20 구성 완료
- Access Port 배정 완료
- Switch ↔ Router Trunk 구성 완료
- Default Gateway 구성 완료
- Router-on-a-Stick 구성 완료
- VLAN 간 통신 확인 완료
- 정상 상태 Packet Tracer 파일 별도 저장 완료

이 환경을 이후 장애 실험과 AI 기반 장애 진단의 정상 기준(Baseline)으로 사용한다.
