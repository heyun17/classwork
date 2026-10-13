from ultralytics import YOLO

#모델 로드
model = YOLO("yolov8n.pt")

#동영상 처리 & 저장
results = model("sample_video.mp4", save=True)

#또는 화면에 바로 보기
# results = model("sample_video.mp4", show=True)