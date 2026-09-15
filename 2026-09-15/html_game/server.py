from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import socket, json, csv, os, threading

LOG_FILE = "game_log.csv"
log_lock = threading.Lock()

class GameHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/log":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))

            with log_lock:
                exists = os.path.exists(LOG_FILE)
                with open(LOG_FILE,"a",newline="",encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    if not exists:
                        w.writerow(["datetime","nickname","client_ip","event","score"])
                    w.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                        data.get("nickname",""),
                        self.client_address[0],
                        data.get("event",""),
                        data.get("score","")
                    ])

            self.send_response(200)
            self.end_headers()
        except Exception as e:
            print("LOG ERROR:", e)
            self.send_error(500)

def get_ip():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8",80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()

ip=get_ip()
server=ThreadingHTTPServer(("0.0.0.0",8000),GameHandler)

print("="*45)
print("HTML GAME SERVER")
print("사용자 2 접속 주소")
print(f"http://{ip}:8000")
print("종료 : Ctrl + C")
print("="*45)

try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
    print("\nServer Stop")