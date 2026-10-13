from ultralytics import YOLO
model = YOLO("yolov8n.pt")
print(model.names)
# 출력
#{0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', ...79: 'toothbrush'
# 이름으로 인덱스번호가 필요하다면
# 이름 → 인덱스
idx = [k for k, v in model.names.items() if v == "person"]
print(idx)  # [0]