import cv2, os, time, psutil
from datetime import datetime
from measure import to_mb, append_row

class WebcamMonitor:
    def __init__(self, index=0, width=1280, height=720,
                 path="logs/resource_log.csv"):
        self.index, self.req_w, self.req_h = index, width, height
        self.path = path
        self.cap = None
        self.rows = []
        self.proc = psutil.Process(os.getpid())

    def __enter__(self):
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError(f"카메라 {self.index} 를 열 수 없습니다")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.req_w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.req_h)
        # 실제로 적용된 값을 읽어 둔다
        self.w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"요청 {self.req_w}x{self.req_h} → 실제 {self.w}x{self.h}")
        self.proc.cpu_percent(interval=None)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.cap is not None:
            self.cap.release()            # 오류가 나도 반드시 반납
        cv2.destroyAllWindows()
        for r in self.rows:
            append_row(r, self.path)
        print(f"{len(self.rows)} 프레임 기록")
        return False
    
    def grab(self, i):
        """프레임 한 장을 가져오며 측정한다."""
        before = to_mb(self.proc.memory_info().rss)
        t0 = time.perf_counter()
        ok, frame = self.cap.read()
        elapsed = time.perf_counter() - t0
        after = to_mb(self.proc.memory_info().rss)

        self.rows.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": f"webcam#{i}", "action": "frame", "lib": "opencv",
            "width": self.w, "height": self.h,
            "mem_before_mb": before, "mem_after_mb": after,
            "mem_delta_mb": round(after - before, 1),
            "cpu_pct": self.proc.cpu_percent(interval=None),
            "elapsed_s": round(elapsed, 4),
        })
        return ok, frame

for w, h in [(640, 480), (1280, 720), (1920, 1080)]:
    try:
        with WebcamMonitor(width=w, height=h) as cam:
            for i in range(100):
                ok, _ = cam.grab(i)
                if not ok:
                    break
    except RuntimeError as e:
        print("건너뜀:", e)
    time.sleep(1)                  # 카메라가 완전히 반납될 시간