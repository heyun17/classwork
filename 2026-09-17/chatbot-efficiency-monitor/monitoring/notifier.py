from __future__ import annotations

import json
import os
from pathlib import Path
import smtplib
from email.message import EmailMessage
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ImportError:  # requirements 설치 전에도 모듈 import 자체는 가능하게 한다.
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]
if load_dotenv is not None:
    load_dotenv(ROOT / ".env")


def send_webhook(message: str) -> tuple[bool, str]:
    """Slack/Teams 계열 Incoming Webhook 알림.

    ALERT_WEBHOOK_URL이 없으면 전송하지 않고 DB 알림 기록만 남긴다.
    """
    url = os.getenv("ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return False, "webhook_not_configured"

    payload = json.dumps({"text": message}).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            ok = 200 <= resp.status < 300
            return ok, f"webhook_http_{resp.status}"
    except Exception as exc:
        # 알림 전송 실패가 모니터 프로세스 자체를 중단시키면 안 된다.
        return False, f"webhook_error:{type(exc).__name__}"


def send_email(subject: str, message: str) -> tuple[bool, str]:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("ALERT_EMAIL_FROM", user).strip()
    recipient = os.getenv("ALERT_EMAIL_TO", "").strip()

    if not (host and sender and recipient):
        return False, "email_not_configured"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(message)

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
        return True, "email_sent"
    except Exception as exc:
        return False, f"email_error:{type(exc).__name__}"


def notify(subject: str, message: str) -> tuple[str, str]:
    """Webhook 우선, 실패/미설정이면 이메일, 둘 다 없으면 DB 기록만 한다."""
    ok, webhook_status = send_webhook(f"*{subject}*\n{message}")
    if ok:
        return "webhook", webhook_status

    ok, email_status = send_email(subject, message)
    if ok:
        return "email", email_status

    return "record_only", f"{webhook_status};{email_status}"
