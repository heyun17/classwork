from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    print("[오류] python-dotenv가 설치되어 있지 않습니다.")
    print("설치: py -m pip install python-dotenv openai")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("[오류] openai 패키지가 설치되어 있지 않습니다.")
    print("설치: py -m pip install python-dotenv openai")
    sys.exit(1)


# ------------------------------------------------------------
# 기본 유틸
# ------------------------------------------------------------

def run_command(cmd: list[str]) -> str:
    """Windows 명령을 실행하고 콘솔 인코딩 문제를 최대한 피해서 문자열로 반환."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=False,
        shell=False,
    )
    raw = result.stdout or b""
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode(errors="replace")


def run_powershell(script: str) -> Any:
    """PowerShell 결과를 JSON으로 받아 로캘에 덜 의존적으로 처리."""
    wrapped = (
        "$ErrorActionPreference='Stop'; "
        "$OutputEncoding=[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
        + script
        + " | ConvertTo-Json -Depth 6 -Compress"
    )
    out = run_command([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", wrapped,
    ]).strip()

    if not out:
        return None

    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def normalize_key(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def parse_netsh_wlan(text: str) -> dict[str, str]:
    """
    netsh wlan show interfaces 출력에서 한국어/영어 필드명을 모두 지원.
    Windows 언어에 따라 라벨이 달라질 수 있어 여러 별칭을 등록한다.
    """
    raw: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        raw[normalize_key(key)] = value.strip()

    aliases = {
        "name": ["이름", "name"],
        "description": ["설명", "description"],
        "guid": ["guid"],
        "mac": ["물리적 주소", "physical address"],
        "state": ["상태", "state"],
        "ssid": ["ssid"],
        "bssid": ["bssid"],
        "network_type": ["네트워크 종류", "network type"],
        "radio_type": ["송수신 장치 종류", "radio type"],
        "authentication": ["인증", "authentication"],
        "cipher": ["암호", "cipher"],
        "connection_mode": ["연결 모드", "connection mode"],
        "channel": ["채널", "channel"],
        "rx_rate": ["수신 속도(mbps)", "receive rate (mbps)"],
        "tx_rate": ["전송 속도(mbps)", "transmit rate (mbps)"],
        "signal": ["신호", "signal"],
        "profile": ["프로필", "profile"],
    }

    result: dict[str, str] = {}
    for canonical, names in aliases.items():
        for name in names:
            v = raw.get(normalize_key(name))
            if v is not None:
                result[canonical] = v
                break
    return result


def infer_band(channel: str | None) -> str:
    if not channel:
        return "확인 불가"
    try:
        ch = int(re.sub(r"\D", "", channel))
    except ValueError:
        return "확인 불가"

    if 1 <= ch <= 14:
        return "2.4 GHz"
    if 32 <= ch <= 177:
        return "5 GHz"
    return "확인 필요"


def first_or_empty(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(x) for x in value if x)
    return str(value)


def safe_float(value: str | None) -> float | None:
    if not value:
        return None
    m = re.search(r"[\d.]+", value)
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


# ------------------------------------------------------------
# 데이터 구조
# ------------------------------------------------------------

@dataclass
class WifiInfo:
    ssid: str = ""
    bssid: str = ""
    protocol: str = ""
    security: str = ""
    cipher: str = ""
    band: str = ""
    channel: str = ""
    rx_mbps: str = ""
    tx_mbps: str = ""
    signal: str = ""
    connection_mode: str = ""
    network_type: str = ""
    ipv4: str = ""
    ipv4_prefix: str = ""
    ipv6_link_local: str = ""
    gateway: str = ""
    dns: str = ""
    dhcp: str = ""
    adapter_name: str = ""
    adapter_description: str = ""
    manufacturer: str = ""
    driver_version: str = ""
    mac: str = ""
    status: str = ""


# ------------------------------------------------------------
# Windows 정보 수집
# ------------------------------------------------------------

def collect_wifi_info() -> WifiInfo:
    netsh_text = run_command(["netsh", "wlan", "show", "interfaces"])
    wlan = parse_netsh_wlan(netsh_text)

    alias = wlan.get("name") or "Wi-Fi"

    ps_script = rf"""
$alias = {json.dumps(alias)}
$adapter = Get-NetAdapter -Name $alias -ErrorAction SilentlyContinue
$ipcfg = Get-NetIPConfiguration -InterfaceAlias $alias -ErrorAction SilentlyContinue
$ipif = Get-NetIPInterface -InterfaceAlias $alias -AddressFamily IPv4 -ErrorAction SilentlyContinue
$dns = Get-DnsClientServerAddress -InterfaceAlias $alias -AddressFamily IPv4 -ErrorAction SilentlyContinue
$drv = $null
if ($adapter) {{
    $drv = Get-CimInstance Win32_PnPSignedDriver |
        Where-Object {{ $_.DeviceName -eq $adapter.InterfaceDescription }} |
        Select-Object -First 1
}}
[PSCustomObject]@{{
    AdapterName = $adapter.Name
    InterfaceDescription = $adapter.InterfaceDescription
    MacAddress = $adapter.MacAddress
    Status = $adapter.Status
    IPv4 = ($ipcfg.IPv4Address.IPAddress -join ', ')
    IPv4Prefix = ($ipcfg.IPv4Address.PrefixLength -join ', ')
    IPv6LinkLocal = ($ipcfg.NetIPv6Interface | ForEach-Object {{
        $idx = $_.InterfaceIndex
        (Get-NetIPAddress -InterfaceIndex $idx -AddressFamily IPv6 -ErrorAction SilentlyContinue |
            Where-Object {{ $_.IPAddress -like 'fe80:*' }} |
            Select-Object -ExpandProperty IPAddress)
    }} | Select-Object -First 1)
    Gateway = ($ipcfg.IPv4DefaultGateway.NextHop -join ', ')
    DNS = ($dns.ServerAddresses -join ', ')
    DHCP = $ipif.Dhcp
    Manufacturer = $drv.Manufacturer
    DriverVersion = $drv.DriverVersion
}}
"""
    ps = run_powershell(ps_script) or {}

    return WifiInfo(
        ssid=wlan.get("ssid", ""),
        bssid=wlan.get("bssid", ""),
        protocol=wlan.get("radio_type", ""),
        security=wlan.get("authentication", ""),
        cipher=wlan.get("cipher", ""),
        band=infer_band(wlan.get("channel")),
        channel=wlan.get("channel", ""),
        rx_mbps=wlan.get("rx_rate", ""),
        tx_mbps=wlan.get("tx_rate", ""),
        signal=wlan.get("signal", ""),
        connection_mode=wlan.get("connection_mode", ""),
        network_type=wlan.get("network_type", ""),
        ipv4=first_or_empty(ps.get("IPv4")),
        ipv4_prefix=first_or_empty(ps.get("IPv4Prefix")),
        ipv6_link_local=first_or_empty(ps.get("IPv6LinkLocal")),
        gateway=first_or_empty(ps.get("Gateway")),
        dns=first_or_empty(ps.get("DNS")),
        dhcp=first_or_empty(ps.get("DHCP")),
        adapter_name=first_or_empty(ps.get("AdapterName")) or alias,
        adapter_description=first_or_empty(ps.get("InterfaceDescription")) or wlan.get("description", ""),
        manufacturer=first_or_empty(ps.get("Manufacturer")),
        driver_version=first_or_empty(ps.get("DriverVersion")),
        mac=first_or_empty(ps.get("MacAddress")) or wlan.get("mac", ""),
        status=first_or_empty(ps.get("Status")) or wlan.get("state", ""),
    )


# ------------------------------------------------------------
# 로컬 이상 여부 판단
# ------------------------------------------------------------

def local_checks(info: WifiInfo) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(item: str, status: str, note: str) -> None:
        checks.append({"item": item, "status": status, "note": note})

    # 연결
    connected_words = ("connected", "연결됨", "up")
    state = (info.status or "").lower()
    if any(x in state for x in connected_words):
        add("연결 상태", "정상", f"Wi-Fi 어댑터 상태: {info.status}")
    else:
        add("연결 상태", "확인 필요", f"현재 상태: {info.status or '값 없음'}")

    # 신호
    signal_num = safe_float(info.signal)
    if signal_num is None:
        add("신호 세기", "확인 필요", "신호 값을 읽지 못했습니다.")
    elif signal_num >= 70:
        add("신호 세기", "정상", f"{signal_num:.0f}% — 양호한 편입니다.")
    elif signal_num >= 50:
        add("신호 세기", "주의", f"{signal_num:.0f}% — 사용 가능하지만 환경 영향이 커질 수 있습니다.")
    else:
        add("신호 세기", "주의", f"{signal_num:.0f}% — 약한 편이라 속도/안정성 저하 가능성이 있습니다.")

    # 보안
    sec = (info.security or "").lower()
    cipher = (info.cipher or "").lower()
    if "wpa3" in sec:
        add("보안", "정상", f"{info.security} / {info.cipher}")
    elif "wpa2" in sec and ("ccmp" in cipher or "aes" in cipher):
        add("보안", "정상", f"{info.security} / {info.cipher} — 일반적으로 사용되는 구성입니다.")
    elif "wep" in sec or "tkip" in cipher or "open" in sec or "개방" in sec:
        add("보안", "주의", f"{info.security} / {info.cipher} — 오래되거나 약한 보안 방식일 수 있습니다.")
    else:
        add("보안", "확인 필요", f"{info.security or '알 수 없음'} / {info.cipher or '알 수 없음'}")

    # 링크 속도
    rx = safe_float(info.rx_mbps)
    tx = safe_float(info.tx_mbps)
    if rx and tx:
        add(
            "Wi-Fi 링크 속도",
            "정보",
            f"수신 {rx:.0f} Mbps / 송신 {tx:.0f} Mbps. 인터넷 실측 처리량과는 다른 값입니다.",
        )
    else:
        add("Wi-Fi 링크 속도", "확인 필요", "RX/TX 링크 속도를 읽지 못했습니다.")

    # DHCP
    dhcp = (info.dhcp or "").lower()
    if dhcp in ("enabled", "활성화됨"):
        add("IPv4 할당", "정상", "DHCP 자동 할당입니다.")
    elif dhcp in ("disabled", "사용 안 함"):
        add("IPv4 할당", "정보", "고정 IPv4 또는 수동 설정일 수 있습니다.")
    else:
        add("IPv4 할당", "정보", f"DHCP: {info.dhcp or '확인 불가'}")

    # DNS
    if info.dns:
        add("DNS", "정상", info.dns)
    else:
        add("DNS", "주의", "IPv4 DNS 서버를 확인하지 못했습니다.")

    # Gateway
    if info.gateway:
        add("기본 게이트웨이", "정상", info.gateway)
    else:
        add("기본 게이트웨이", "주의", "IPv4 기본 게이트웨이를 확인하지 못했습니다.")

    return checks


# ------------------------------------------------------------
# GPT 인사이트
# ------------------------------------------------------------

def get_gpt_insight(info: WifiInfo, checks: list[dict[str, str]]) -> str:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()

    if not api_key:
        return (
            "[GPT 인사이트 생략]\n"
            ".env에 OPENAI_API_KEY가 없습니다.\n"
            "예: OPENAI_API_KEY=sk-...\n"
            f"현재 기본 모델값: {model}"
        )

    payload = {
        "wifi_info": asdict(info),
        "local_checks": checks,
    }

    prompt = f"""
당신은 Windows 네트워크 진단 보조자입니다.
아래 값은 사용자의 현재 Windows Wi-Fi 연결 상태를 로컬 명령으로 수집한 결과입니다.

반드시 다음 규칙을 지키세요.
1. 한국어로 답하세요.
2. 실제 관측값과 추론을 구분하세요.
3. 링크 속도(RX/TX Mbps)를 인터넷 다운로드/업로드 실측 속도라고 부르지 마세요.
4. 이 데이터만으로 확인할 수 없는 대역폭 병목, 인터넷 처리량, 잡음, 간섭, 회선 품질을 단정하지 마세요.
5. 드라이버 버전은 최신 여부를 외부 조회하지 않았으므로 '최신/구형'이라고 단정하지 마세요.
6. 이상이 없다면 억지로 문제를 만들지 마세요.
7. 출력 형식:
   - 종합 상태: 1~2문장
   - 주요 인사이트: 최대 5개
   - 확인 필요 사항: 실제로 추가 측정이 필요한 것만 최대 3개

데이터:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text.strip()


# ------------------------------------------------------------
# 출력
# ------------------------------------------------------------

def print_markdown_table(info: WifiInfo) -> None:
    rows = [
        ("SSID", info.ssid),
        ("BSSID", info.bssid),
        ("프로토콜", info.protocol),
        ("보안 종류", info.security),
        ("암호", info.cipher),
        ("네트워크 대역", info.band),
        ("채널", info.channel),
        ("링크 속도 RX/TX", f"{info.rx_mbps} / {info.tx_mbps} Mbps"),
        ("신호", info.signal),
        ("연결 모드", info.connection_mode),
        ("네트워크 종류", info.network_type),
        ("IPv4", f"{info.ipv4}/{info.ipv4_prefix}" if info.ipv4_prefix else info.ipv4),
        ("IPv6 Link-local", info.ipv6_link_local),
        ("기본 게이트웨이", info.gateway),
        ("DNS", info.dns),
        ("DHCP", info.dhcp),
        ("어댑터 이름", info.adapter_name),
        ("어댑터 설명", info.adapter_description),
        ("제조업체", info.manufacturer),
        ("드라이버 버전", info.driver_version),
        ("MAC", info.mac),
        ("어댑터 상태", info.status),
    ]

    print("\n=== Wi-Fi 속성 요약 ===")
    print("| 항목 | 값 |")
    print("|---|---|")
    for k, v in rows:
        value = str(v or "확인 불가").replace("|", r"\|")
        print(f"| {k} | {value} |")


def print_checks(checks: list[dict[str, str]]) -> None:
    print("\n=== 로컬 이상 여부 확인 ===")
    print("| 항목 | 상태 | 설명 |")
    print("|---|---|---|")
    for c in checks:
        note = c["note"].replace("|", r"\|")
        print(f"| {c['item']} | {c['status']} | {note} |")


def main() -> None:
    if os.name != "nt":
        print("[오류] 이 프로그램은 Windows용입니다.")
        sys.exit(1)

    print("Windows Wi-Fi 정보를 수집하는 중...")
    info = collect_wifi_info()

    if not info.ssid and not info.ipv4:
        print("[오류] 연결된 Wi-Fi 정보를 찾지 못했습니다.")
        print("Wi-Fi 연결 상태와 'netsh wlan show interfaces' 결과를 확인하세요.")
        sys.exit(1)

    checks = local_checks(info)

    print_markdown_table(info)
    print_checks(checks)

    print("\n=== GPT 인사이트 ===")
    try:
        print(get_gpt_insight(info, checks))
    except Exception as e:
        print(f"[GPT API 오류] {e}")
        print("로컬 Wi-Fi 수집/이상 여부 확인 결과는 위 표에서 계속 사용할 수 있습니다.")


if __name__ == "__main__":
    main()
