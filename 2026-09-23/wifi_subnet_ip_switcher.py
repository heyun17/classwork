from __future__ import annotations

import ctypes
import ipaddress
import platform
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import pandas as pd
import psutil
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None


IS_WINDOWS = platform.system().lower() == "windows"
MAX_SCAN_HOSTS = 2048


@dataclass
class IPv4Interface:
    name: str
    is_up: bool
    speed_mbps: int
    mac: str
    ip: str
    netmask: str
    cidr: int
    network: str
    broadcast: str
    first_host: str
    last_host: str
    usable_hosts: int
    gateway: str = ""
    dns_servers: tuple[str, ...] = ()


def run_hidden(command: list[str], timeout: float = 8.0) -> subprocess.CompletedProcess:
    kwargs = {
        "capture_output": True,
        "text": True,
        "errors": "ignore",
        "timeout": timeout,
    }
    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(command, **kwargs)


def is_admin() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def normalize_mac(mac: str) -> str:
    if not mac:
        return ""
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", mac)
    if len(cleaned) != 12:
        return mac.upper()
    return "-".join(cleaned[i:i + 2] for i in range(0, 12, 2)).upper()


def ps_quote(value: str) -> str:
    return value.replace("'", "''")


def get_dns_servers(interface_name: str) -> tuple[str, ...]:
    if not IS_WINDOWS:
        return ()
    try:
        cmd = (
            "$x=(Get-DnsClientServerAddress "
            f"-InterfaceAlias '{ps_quote(interface_name)}' "
            "-AddressFamily IPv4 -ErrorAction Stop).ServerAddresses;"
            "$x -join ','"
        )
        result = run_hidden(
            ["powershell", "-NoProfile", "-Command", cmd],
            timeout=6.0,
        )
        if result.returncode == 0:
            values = [x.strip() for x in result.stdout.strip().split(",") if x.strip()]
            return tuple(values)
    except Exception:
        pass
    return ()


def get_default_routes() -> list[dict]:
    routes = []
    if not IS_WINDOWS:
        return routes
    try:
        result = run_hidden(["route", "print", "-4"], timeout=5.0)
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                try:
                    metric = int(parts[4])
                except ValueError:
                    metric = 999999
                routes.append(
                    {
                        "gateway": parts[2],
                        "interface_ip": parts[3],
                        "metric": metric,
                    }
                )
    except Exception:
        pass
    return sorted(routes, key=lambda x: x["metric"])


def get_interfaces() -> list[IPv4Interface]:
    stats = psutil.net_if_stats()
    addresses = psutil.net_if_addrs()
    routes = get_default_routes()
    rows: list[IPv4Interface] = []

    for name, addr_list in addresses.items():
        stat = stats.get(name)
        is_up = bool(stat.isup) if stat else False
        speed = int(stat.speed) if stat and stat.speed and stat.speed > 0 else 0

        mac = ""
        for addr in addr_list:
            if getattr(psutil, "AF_LINK", object()) == addr.family:
                mac = normalize_mac(addr.address)
                break

        for addr in addr_list:
            if addr.family != socket.AF_INET:
                continue
            if not addr.address or addr.address.startswith("127."):
                continue
            if not addr.netmask:
                continue

            try:
                net = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
            except ValueError:
                continue

            if net.prefixlen <= 30:
                first_host = str(net.network_address + 1)
                last_host = str(net.broadcast_address - 1)
                usable = max(net.num_addresses - 2, 0)
            elif net.prefixlen == 31:
                first_host = str(net.network_address)
                last_host = str(net.broadcast_address)
                usable = 2
            else:
                first_host = str(net.network_address)
                last_host = str(net.network_address)
                usable = 1

            gateway = ""
            matched = [r for r in routes if r["interface_ip"] == addr.address]
            if matched:
                gateway = matched[0]["gateway"]

            rows.append(
                IPv4Interface(
                    name=name,
                    is_up=is_up,
                    speed_mbps=speed,
                    mac=mac,
                    ip=addr.address,
                    netmask=addr.netmask,
                    cidr=net.prefixlen,
                    network=str(net.network_address),
                    broadcast=str(net.broadcast_address),
                    first_host=first_host,
                    last_host=last_host,
                    usable_hosts=usable,
                    gateway=gateway,
                    dns_servers=get_dns_servers(name),
                )
            )
    return rows


def choose_primary_index(interfaces: list[IPv4Interface]) -> int:
    for i, nic in enumerate(interfaces):
        if nic.is_up and nic.gateway and ("wi-fi" in nic.name.lower() or "wireless" in nic.name.lower()):
            return i
    for i, nic in enumerate(interfaces):
        if nic.is_up and nic.gateway:
            return i
    for i, nic in enumerate(interfaces):
        if nic.is_up:
            return i
    return 0


def ping_host(ip: str, timeout_ms: int = 250) -> bool:
    try:
        if IS_WINDOWS:
            result = run_hidden(
                ["ping", "-n", "1", "-w", str(timeout_ms), ip],
                timeout=max(1.0, timeout_ms / 1000 + 0.8),
            )
        else:
            timeout_s = max(1, int(round(timeout_ms / 1000)))
            result = run_hidden(
                ["ping", "-c", "1", "-W", str(timeout_s), ip],
                timeout=timeout_s + 1.0,
            )
        return result.returncode == 0
    except Exception:
        return False


def get_arp_table() -> dict[str, str]:
    arp: dict[str, str] = {}
    try:
        result = run_hidden(["arp", "-a"], timeout=5.0)
        ipv4_pat = r"(?:\d{1,3}\.){3}\d{1,3}"
        mac_pat = r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}"

        for line in result.stdout.splitlines():
            ip_match = re.search(ipv4_pat, line)
            mac_match = re.search(mac_pat, line)
            if ip_match and mac_match:
                arp[ip_match.group(0)] = normalize_mac(mac_match.group(0))
    except Exception:
        pass
    return arp


def scan_availability(
    nic: IPv4Interface,
    timeout_ms: int,
    workers: int,
) -> pd.DataFrame:
    net = ipaddress.IPv4Network(f"{nic.ip}/{nic.cidr}", strict=False)
    hosts = [str(x) for x in net.hosts()]

    if len(hosts) > MAX_SCAN_HOSTS:
        raise ValueError(
            f"호스트가 {len(hosts):,}개입니다. "
            f"안전을 위해 최대 {MAX_SCAN_HOSTS:,}개까지만 자동 검사합니다."
        )

    reserved = {nic.ip}
    if nic.gateway:
        reserved.add(nic.gateway)

    ping_results: dict[str, bool] = {}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(ping_host, ip, timeout_ms): ip
            for ip in hosts
            if ip not in reserved
        }
        for future in as_completed(futures):
            ip = futures[future]
            try:
                ping_results[ip] = bool(future.result())
            except Exception:
                ping_results[ip] = False

    # A local-subnet ping normally causes ARP resolution first.  Therefore an
    # ARP entry is useful even when a host blocks ICMP echo replies.
    arp = get_arp_table()

    rows = []
    for ip in hosts:
        if ip == nic.ip:
            status = "내 PC"
            candidate = False
            reason = "현재 사용 중"
            mac = nic.mac
        elif nic.gateway and ip == nic.gateway:
            status = "게이트웨이"
            candidate = False
            reason = "기본 게이트웨이"
            mac = arp.get(ip, "")
        else:
            ping_ok = ping_results.get(ip, False)
            mac = arp.get(ip, "")

            if ping_ok:
                status = "사용 중 감지"
                candidate = False
                reason = "Ping 응답"
            elif mac:
                status = "사용 중 추정"
                candidate = False
                reason = "ARP/Neighbor 감지"
            else:
                status = "미사용 추정"
                candidate = True
                reason = "Ping/ARP에서 감지되지 않음"

        rows.append(
            {
                "IP": ip,
                "상태": status,
                "변경 후보": "가능" if candidate else "",
                "근거": reason,
                "MAC": mac,
            }
        )
    return pd.DataFrame(rows)


def final_conflict_check(ip: str, timeout_ms: int = 500) -> tuple[bool, str]:
    """
    Return (conflict_detected, message).
    This is intentionally conservative: any Ping reply or ARP entry is treated
    as a conflict. No method can prove an address is permanently free without
    authoritative DHCP/IPAM information.
    """
    ping_ok = ping_host(ip, timeout_ms)
    time.sleep(0.15)
    arp = get_arp_table()
    mac = arp.get(ip, "")

    if ping_ok:
        return True, "Ping 응답이 있어 사용 중으로 판단했습니다."
    if mac:
        return True, f"ARP에서 MAC {mac}가 확인되어 사용 중으로 판단했습니다."
    return False, "Ping/ARP에서 충돌 징후를 찾지 못했습니다."


def set_static_ipv4(
    nic: IPv4Interface,
    new_ip: str,
    dns_servers: tuple[str, ...],
) -> tuple[bool, str]:
    if not IS_WINDOWS:
        return False, "이 기능은 Windows용입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."

    if not nic.gateway:
        return False, "기본 게이트웨이를 찾지 못해 변경하지 않았습니다."

    cmd = [
        "netsh", "interface", "ipv4", "set", "address",
        f"name={nic.name}",
        "source=static",
        f"address={new_ip}",
        f"mask={nic.netmask}",
        f"gateway={nic.gateway}",
        "gwmetric=1",
    ]
    result = run_hidden(cmd, timeout=15.0)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "IP 변경 실패").strip()

    # Preserve the currently detected IPv4 DNS servers as static DNS.
    if dns_servers:
        primary = dns_servers[0]
        dns_cmd = [
            "netsh", "interface", "ipv4", "set", "dnsservers",
            f"name={nic.name}",
            "source=static",
            f"address={primary}",
            "register=primary",
            "validate=no",
        ]
        run_hidden(dns_cmd, timeout=10.0)

        for index, server in enumerate(dns_servers[1:], start=2):
            add_cmd = [
                "netsh", "interface", "ipv4", "add", "dnsservers",
                f"name={nic.name}",
                f"address={server}",
                f"index={index}",
                "validate=no",
            ]
            run_hidden(add_cmd, timeout=10.0)

    return True, f"{nic.name}의 IPv4를 {new_ip}/{nic.cidr}로 설정했습니다."


def restore_dhcp(interface_name: str) -> tuple[bool, str]:
    if not IS_WINDOWS:
        return False, "이 기능은 Windows용입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."

    addr = run_hidden(
        [
            "netsh", "interface", "ipv4", "set", "address",
            f"name={interface_name}",
            "source=dhcp",
        ],
        timeout=15.0,
    )
    dns = run_hidden(
        [
            "netsh", "interface", "ipv4", "set", "dnsservers",
            f"name={interface_name}",
            "source=dhcp",
        ],
        timeout=15.0,
    )

    if addr.returncode == 0 and dns.returncode == 0:
        return True, f"{interface_name}를 DHCP 주소/DNS 자동 할당으로 복구했습니다."

    msg = "\n".join(
        x for x in [
            addr.stderr or addr.stdout,
            dns.stderr or dns.stdout,
        ] if x
    ).strip()
    return False, msg or "DHCP 복구에 실패했습니다."


st.set_page_config(
    page_title="Wi-Fi Subnet IP Switcher",
    page_icon="📡",
    layout="wide",
)

st.title("📡 Wi-Fi Subnet IP Monitor & Switcher")
st.caption(
    "현재 서브넷을 검사해 사용 중으로 감지되지 않은 IPv4 후보를 보여주고, "
    "선택한 주소를 Windows 무선 인터페이스에 적용합니다."
)

if not IS_WINDOWS:
    st.error("이 버전의 IP 변경 기능은 Windows용입니다.")
    st.stop()

with st.sidebar:
    st.header("모니터링 설정")
    auto_refresh = st.toggle("자동 새로고침", value=False)
    refresh_seconds = st.slider("새로고침 주기(초)", 3, 60, 10)

    st.divider()
    st.subheader("스캔 설정")
    timeout_ms = st.slider("Ping timeout (ms)", 100, 1200, 300, step=50)
    workers = st.slider("동시 검사 수", 8, 128, 64, step=8)

if auto_refresh and st_autorefresh is not None:
    st_autorefresh(interval=refresh_seconds * 1000, key="autorefresh")

interfaces = get_interfaces()
if not interfaces:
    st.error("IPv4 주소가 설정된 네트워크 인터페이스를 찾지 못했습니다.")
    st.stop()

primary_idx = choose_primary_index(interfaces)
labels = [
    f"{x.name} — {x.ip}/{x.cidr} — {'UP' if x.is_up else 'DOWN'}"
    for x in interfaces
]
selected_label = st.selectbox(
    "대상 인터페이스",
    labels,
    index=min(primary_idx, len(labels) - 1),
)
nic = interfaces[labels.index(selected_label)]
network = ipaddress.IPv4Network(f"{nic.ip}/{nic.cidr}", strict=False)

admin = is_admin()
admin_text = "관리자 권한" if admin else "일반 권한"

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("인터페이스", nic.name)
m2.metric("상태", "UP" if nic.is_up else "DOWN")
m3.metric("IPv4 / CIDR", f"{nic.ip}/{nic.cidr}")
m4.metric("Network", f"{nic.network}/{nic.cidr}")
m5.metric("MAC", nic.mac or "미확인")
m6.metric("실행 권한", admin_text)

st.info(
    f"가용 범위: **{nic.first_host} ~ {nic.last_host}** "
    f"({nic.usable_hosts:,} hosts) · "
    f"Gateway: **{nic.gateway or '미확인'}** · "
    f"DNS: **{', '.join(nic.dns_servers) if nic.dns_servers else '미확인'}**"
)

if not admin:
    st.warning(
        "조회와 스캔은 가능하지만 IP 변경/DHCP 복구는 관리자 권한이 필요합니다. "
        "PowerShell을 '관리자 권한으로 실행'한 뒤 Streamlit을 실행하세요."
    )

st.warning(
    "중요: '미사용 추정'은 현재 Ping/ARP에서 장비가 감지되지 않았다는 뜻입니다. "
    "DHCP 서버의 임대 풀/예약 정보를 확인하지 않는 한 미래의 IP 충돌까지 보장할 수 없습니다. "
    "관리되는 네트워크에서는 관리자에게 할당받은 고정 IP 또는 DHCP 예약 주소를 사용하는 것이 안전합니다."
)

scan_key = f"scan::{nic.name}::{nic.network}/{nic.cidr}"

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    scan_clicked = st.button("🔎 가용 IP 후보 찾기", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 결과 지우기", use_container_width=True):
        st.session_state.pop(scan_key, None)
        st.rerun()
with c3:
    st.caption(
        "네트워크 주소/브로드캐스트/현재 IP/게이트웨이는 변경 후보에서 자동 제외합니다."
    )

if scan_clicked:
    if not network.is_private:
        st.error("자동 스캔은 사설 IPv4 네트워크에서만 실행하도록 제한했습니다.")
    elif nic.usable_hosts > MAX_SCAN_HOSTS:
        st.error(
            f"현재 서브넷은 {nic.usable_hosts:,}개 호스트입니다. "
            f"자동 검사 상한은 {MAX_SCAN_HOSTS:,}개입니다."
        )
    else:
        with st.spinner("현재 서브넷을 검사하는 중..."):
            try:
                df = scan_availability(nic, timeout_ms, workers)
                st.session_state[scan_key] = df
            except Exception as exc:
                st.error(f"스캔 실패: {exc}")

df = st.session_state.get(scan_key)

if df is not None:
    used_count = int((df["변경 후보"] != "가능").sum())
    candidate_df = df[df["변경 후보"] == "가능"].copy()
    candidate_count = len(candidate_df)

    s1, s2, s3 = st.columns(3)
    s1.metric("전체 가용 호스트 주소", f"{len(df):,}")
    s2.metric("사용/예약 감지", f"{used_count:,}")
    s3.metric("미사용 추정 후보", f"{candidate_count:,}")

    tabs = st.tabs(["변경 후보", "전체 스캔 결과"])

    with tabs[0]:
        st.dataframe(
            candidate_df[["IP", "상태", "근거"]],
            hide_index=True,
            use_container_width=True,
            height=360,
        )

    with tabs[1]:
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            height=420,
        )

    st.divider()
    st.subheader("선택한 주소로 변경")

    candidates = candidate_df["IP"].tolist()

    if not candidates:
        st.warning("현재 검사 결과에서 변경 후보가 없습니다.")
    else:
        selected_ip = st.selectbox(
            "적용할 IPv4 주소",
            candidates,
            index=0,
        )

        net = ipaddress.IPv4Network(f"{selected_ip}/{nic.cidr}", strict=False)
        st.code(
            "\n".join(
                [
                    f"Interface : {nic.name}",
                    f"New IPv4   : {selected_ip}",
                    f"CIDR       : /{nic.cidr}",
                    f"Mask       : {nic.netmask}",
                    f"Network    : {net.network_address}/{nic.cidr}",
                    f"Gateway    : {nic.gateway or '미확인'}",
                    f"DNS        : {', '.join(nic.dns_servers) if nic.dns_servers else '미확인'}",
                    f"MAC        : {nic.mac or '미확인'}",
                ]
            ),
            language="text",
        )

        confirm = st.checkbox(
            "선택한 주소에 대해 최종 충돌 검사를 다시 수행한 뒤 정적 IPv4로 변경하는 것에 동의합니다."
        )

        if st.button(
            "✅ 최종 검사 후 IP 변경",
            disabled=not (confirm and admin),
            type="primary",
        ):
            with st.spinner("선택 주소를 다시 검사하고 있습니다..."):
                conflict, detail = final_conflict_check(selected_ip, max(timeout_ms, 500))

            if conflict:
                st.error(f"변경 중단: {detail}")
            else:
                with st.spinner("Windows 네트워크 설정을 변경하는 중..."):
                    ok, message = set_static_ipv4(
                        nic=nic,
                        new_ip=selected_ip,
                        dns_servers=nic.dns_servers,
                    )

                if ok:
                    st.success(message)
                    st.info(
                        "네트워크 연결이 잠시 끊겼다가 복구될 수 있습니다. "
                        "현재 Streamlit은 localhost에서 실행되므로 브라우저 페이지 자체는 유지됩니다."
                    )
                    st.session_state.pop(scan_key, None)
                    time.sleep(2.0)
                    st.rerun()
                else:
                    st.error(message)
else:
    st.info("먼저 **가용 IP 후보 찾기**를 실행하세요.")

st.divider()
st.subheader("DHCP 자동 할당으로 복구")

restore_confirm = st.checkbox(
    "현재 인터페이스를 DHCP 주소 및 DNS 자동 할당으로 복구할 준비가 되었습니다.",
    key="dhcp_confirm",
)

if st.button(
    "↩️ DHCP로 복구",
    disabled=not (restore_confirm and admin),
):
    with st.spinner("DHCP 설정으로 복구하는 중..."):
        ok, message = restore_dhcp(nic.name)

    if ok:
        st.success(message)
        st.session_state.pop(scan_key, None)
        time.sleep(2.0)
        st.rerun()
    else:
        st.error(message)

st.divider()
st.subheader("전체 IPv4 인터페이스")

all_df = pd.DataFrame(
    [
        {
            "인터페이스": x.name,
            "상태": "UP" if x.is_up else "DOWN",
            "IPv4": x.ip,
            "CIDR": f"/{x.cidr}",
            "Network": f"{x.network}/{x.cidr}",
            "Gateway": x.gateway,
            "MAC": x.mac,
            "DNS": ", ".join(x.dns_servers),
        }
        for x in get_interfaces()
    ]
)
st.dataframe(all_df, hide_index=True, use_container_width=True)

st.caption(
    "IP 변경은 현재 선택한 인터페이스에만 적용됩니다. "
    "Hyper-V vEthernet 같은 가상 NIC는 필요하지 않으면 선택하지 마세요."
)
