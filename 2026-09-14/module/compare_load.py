import os, re, gc
from PIL import Image
import cv2
from measure import ResourceLogger, parse_name

IMG_DIR = "images"

def load_pillow(path):
    img = Image.open(path)
    img.load()                    # ← 실제로 픽셀을 읽게 만든다
    return img

def load_opencv(path):
    return cv2.imread(path)       # 부르는 즉시 전부 읽음

with ResourceLogger() as logger:
    for f in sorted(os.listdir(IMG_DIR)):
        if not f.lower().endswith((".jpg", ".png")):
            continue
        path = os.path.join(IMG_DIR, f)
        w, h = parse_name(f)          # STEP 2 의 정규표현식

        for lib, fn in (("pillow", load_pillow), ("opencv", load_opencv)):
            gc.collect()                # 이전 측정의 잔여물 정리
            img = logger.measure(
                lambda: fn(path),
                target=f, action="load", lib=lib, width=w, height=h,
            )
            del img                  # 참조를 끊어 다음 측정에 영향 줄이기