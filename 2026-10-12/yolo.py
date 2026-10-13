import cv2
import matplotlib.pyplot as plt
import urllib.request
import numpy as np
from ultralytics import YOLO

# 1. URL에서 이미지 직접 읽어오기
url = "https://www.jejunews.com/news/photo/201511/1974230_110132_2918.jpg"
req = urllib.request.urlopen(url)
arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

# 2. YOLO 기본 모델로 이미지 직접 탐지 (Inference)
model = YOLO("yolov8n.pt") 
results = model(img)

# 3. YOLO 내장 함수로 박스 자동 시각화
plot_img = results[0].plot()

# 4. 출력
plt.figure(figsize=(10, 8))
plt.imshow(cv2.cvtColor(plot_img, cv2.COLOR_BGR2RGB))
plt.axis('on')
plt.show()