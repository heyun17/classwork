from ultralytics import YOLO

model = YOLO("yolov8n.pt")
results = model.predict("1974230_110132_2918.jpg", conf=0.25)

# result 모델에서 받는것
# result[0]의 인자중에서 boxes ⇒분류, 신뢰도, 박스위치등의 정보가 있음.
# 예) 분류에 사람이 없다면, 또는 사람이 있다면
for r in results:
    boxes = r.boxes
    for box in boxes:
        cls_id    = int(box.cls)                  # 클래스 인덱스 (숫자)
        cls_name  = model.names[cls_id]           # 클래스 이름 (문자열)
        conf      = round(float(box.conf), 2)     # confidence
        x1,y1,x2,y2 = box.xyxy[0].tolist()       # 좌표 (좌상단, 우하단)

        print(f"{cls_name} | conf: {conf} | box: {x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}")