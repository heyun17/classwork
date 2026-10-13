from ultralytics import YOLO

model = YOLO("yolov8n.pt")
data="1974230_110132_2918.jpg"
results = model.predict(data)
r=results[0]

print(r.boxes)
