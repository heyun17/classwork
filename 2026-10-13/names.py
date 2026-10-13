from ultralytics import YOLO
from PIL import Image
import numpy as np

model = YOLO('yolov8n-pose.pt')

# 키포인트 이름 정의
KEYPOINT_NAMES = [
    '코',                                    # 0
    '왼눈', '오른눈',                         # 1, 2
    '왼귀', '오른귀',                         # 3, 4
    '왼어깨', '오른어깨',                      # 5, 6
    '왼팔꿈치', '오른팔꿈치',                  # 7, 8
    '왼손목', '오른손목',                      # 9, 10
    '왼골반', '오른골반',                      # 11, 12
    '왼무릎', '오른무릎',                      # 13, 14
    '왼발목', '오른발목'                       # 15, 16
]