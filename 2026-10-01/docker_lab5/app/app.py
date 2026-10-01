"""아주 작은 웹 앱. 자기 호스트명(컨테이너/파드 이름)을 보여 준다.
  /          : 이름과 상태 표시
  /healthz   : 헬스 체크용
  /kill      : 일부러 앱을 죽인다 (장애 실습용)
"""
import os, socket, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer

NAME = os.environ.get("APP_NAME", "app")
PORT = int(os.environ.get("PORT", "8000"))
healthy = True

PAGE = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>{name}</title></head><body>
<h1>{name}</h1>
<p>호스트명 : <b>{host}</b></p>
<p>상태 : {state}</p>
<p><a href="/kill">앱 죽이기 (/kill)</a> · <a href="/healthz">헬스 체크 (/healthz)</a></p>
</body></html>"""

class H(BaseHTTPRequestHandler):
    def _send(self, body, status=200, ctype="text/html; charset=utf-8"):
        b = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        global healthy
        host = socket.gethostname()
        if self.path.startswith("/healthz"):
            self._send("ok" if healthy else "sick", 200 if healthy else 500, "text/plain")
        elif self.path.startswith("/kill"):
            healthy = False
            self._send("이제 이 앱은 아프다고 응답합니다. 곧 종료됩니다.", 200, "text/plain")
            threading.Thread(target=lambda: (time.sleep(3), os._exit(1))).start()
        else:
            state = "정상" if healthy else "비정상"
            self._send(PAGE.format(name=NAME, host=host, state=state))

    def log_message(self, fmt, *args):
        print(f"[{NAME}] {self.address_string()} {fmt % args}", flush=True)

if __name__ == "__main__":
    print(f"[{NAME}] start on :{PORT} host={socket.gethostname()}", flush=True)
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
