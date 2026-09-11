import cv2
import mediapipe as mp
import os


# ========================================
# 설정
# ========================================

IMAGE_PATH = "face.png"
OUTPUT_PATH = "face_landmarks.jpg"
MODEL_PATH = "face_landmarker.task"

# 작은 사진은 랜드마크 번호가 잘 안 보이므로 확대
MIN_WIDTH = 1000


# ========================================
# 이미지 불러오기
# ========================================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print(f"이미지를 찾을 수 없습니다: {IMAGE_PATH}")
    raise SystemExit


# 이미지가 작으면 확대
height, width = image.shape[:2]

if width < MIN_WIDTH:
    scale = MIN_WIDTH / width

    image = cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )


height, width = image.shape[:2]


# ========================================
# MediaPipe Face Landmarker 설정
# ========================================

base_options = mp.tasks.BaseOptions(model_asset_path=MODEL_PATH)
face_landmarker_options = mp.tasks.vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=mp.tasks.vision.RunningMode.IMAGE,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5
)


# OpenCV BGR -> RGB 변환
rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

with mp.tasks.vision.FaceLandmarker.create_from_options(face_landmarker_options) as face_landmarker:
    result = face_landmarker.detect(mp_image)


# ========================================
# 얼굴을 찾지 못한 경우
# ========================================

if not result.face_landmarks:
    print("얼굴을 찾지 못했습니다.")
    raise SystemExit


# 현재 Face Landmarker는 홍채 포함 478개를 반환할 수 있으므로 기본 468개만 표시
landmarks = result.face_landmarks[0][:468]


# ========================================
# 얼굴 Mesh 연결선 그리기
# ========================================

# 첨부 이미지와 비슷한 녹색
line_color = (0, 180, 0)
point_color = (0, 130, 0)
text_color = (0, 150, 0)


for connection in mp.tasks.vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION:

    start_idx = connection.start
    end_idx = connection.end

    if start_idx >= len(landmarks) or end_idx >= len(landmarks):
        continue

    start = landmarks[start_idx]
    end = landmarks[end_idx]

    x1 = int(start.x * width)
    y1 = int(start.y * height)

    x2 = int(end.x * width)
    y2 = int(end.y * height)

    cv2.line(
        image,
        (x1, y1),
        (x2, y2),
        line_color,
        1,
        cv2.LINE_AA
    )


# ========================================
# 각 랜드마크 점 + 번호 출력
# ========================================

for index, landmark in enumerate(landmarks):

    x = int(landmark.x * width)
    y = int(landmark.y * height)

    # 랜드마크 점
    cv2.circle(
        image,
        (x, y),
        1,
        point_color,
        -1
    )

    # 랜드마크 번호
    cv2.putText(
        image,
        str(index),
        (x + 2, y - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.28,
        text_color,
        1,
        cv2.LINE_AA
    )


# ========================================
# 얼굴 중앙 기준선
# ========================================

center_x = width // 2

cv2.line(
    image,
    (center_x, 0),
    (center_x, height),
    (160, 160, 160),
    1
)


# ========================================
# 결과 저장
# ========================================

cv2.imwrite(OUTPUT_PATH, image)

print(f"랜드마크 개수: {len(landmarks)}")
print(f"결과 저장 완료: {os.path.abspath(OUTPUT_PATH)}")


# ========================================
# 화면에 결과 표시
# ========================================

# 화면 표시용으로 너무 크면 축소
display = image.copy()

max_height = 900

if display.shape[0] > max_height:
    ratio = max_height / display.shape[0]

    display = cv2.resize(
        display,
        None,
        fx=ratio,
        fy=ratio
    )


cv2.imshow("MediaPipe Face Landmark Index", display)

print("아무 키나 누르면 종료됩니다.")

cv2.waitKey(0)
cv2.destroyAllWindows()

