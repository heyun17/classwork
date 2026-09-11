from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


# ========================================
# 파일 설정
# ========================================

PROJECT_DIR = Path(__file__).resolve().parent
IMAGE_PATH = PROJECT_DIR / "face.png"
FLAME_PATH = PROJECT_DIR / "426833.png"
MODEL_PATH = PROJECT_DIR / "face_landmarker.task"
OUTPUT_PATH = PROJECT_DIR / "face_with_fire.png"


# MediaPipe Face Landmarker의 홍채 랜드마크 인덱스
# 468~472: 한쪽 홍채, 473~477: 다른 쪽 홍채
IRIS_GROUPS = (
    (468, 469, 470, 471, 472),
    (473, 474, 475, 476, 477),
)


def check_input_files():
    """필요한 입력 파일이 있는지 확인한다."""
    for path in (IMAGE_PATH, FLAME_PATH, MODEL_PATH):
        if not path.is_file():
            print(f"필요한 파일을 찾을 수 없습니다: {path.name}")
            raise SystemExit(1)


def read_image(path, flags):
    """한글이 포함된 Windows 경로에서도 이미지를 읽는다."""
    image_bytes = np.fromfile(str(path), dtype=np.uint8)
    if image_bytes.size == 0:
        return None
    return cv2.imdecode(image_bytes, flags)


def write_image(path, image):
    """한글이 포함된 Windows 경로에서도 이미지를 저장한다."""
    success, encoded = cv2.imencode(path.suffix, image)
    if not success:
        return False
    encoded.tofile(str(path))
    return True


def get_iris_center_and_diameter(landmarks, indices, width, height):
    """홍채 랜드마크에서 중심 좌표와 홍채 지름을 계산한다."""
    points = np.array(
        [(landmarks[index].x * width, landmarks[index].y * height) for index in indices],
        dtype=np.float32,
    )

    center, radius = cv2.minEnclosingCircle(points)
    return (int(round(center[0])), int(round(center[1]))), max(2.0 * radius, 1.0)


def make_flame_alpha(flame):
    """불꽃 PNG의 투명도 채널을 만들고 흰색 배경을 제거한다."""
    if flame.shape[2] == 4:
        flame_bgr = flame[:, :, :3]
        alpha = flame[:, :, 3].astype(np.float32) / 255.0
    else:
        flame_bgr = flame
        # 426833.png의 흰색 배경을 투명하게 만든다.
        non_white = np.min(flame_bgr, axis=2) < 245
        alpha = non_white.astype(np.float32)

    return flame_bgr, alpha


def overlay_flame(image, flame_bgr, flame_alpha, center, diameter):
    """불꽃을 눈동자 중심에 맞춰 크기 조절 후 이미지 위에 합성한다."""
    # 불꽃이 눈동자를 충분히 덮도록 홍채 지름보다 조금 크게 맞춘다.
    target_size = max(int(round(diameter * 1.35)), 12)

    resized_flame = cv2.resize(
        flame_bgr,
        (target_size, target_size),
        interpolation=cv2.INTER_AREA,
    )
    resized_alpha = cv2.resize(
        flame_alpha,
        (target_size, target_size),
        interpolation=cv2.INTER_AREA,
    )

    center_x, center_y = center
    left = center_x - target_size // 2
    top = center_y - target_size // 2
    right = left + target_size
    bottom = top + target_size

    # 이미지 바깥으로 나가는 부분은 잘라서 처리한다.
    image_left = max(left, 0)
    image_top = max(top, 0)
    image_right = min(right, image.shape[1])
    image_bottom = min(bottom, image.shape[0])

    if image_left >= image_right or image_top >= image_bottom:
        return

    flame_left = image_left - left
    flame_top = image_top - top
    flame_right = flame_left + (image_right - image_left)
    flame_bottom = flame_top + (image_bottom - image_top)

    roi = image[image_top:image_bottom, image_left:image_right].astype(np.float32)
    flame_roi = resized_flame[flame_top:flame_bottom, flame_left:flame_right].astype(
        np.float32
    )
    alpha_roi = resized_alpha[flame_top:flame_bottom, flame_left:flame_right]

    # 가장자리의 반투명 픽셀까지 자연스럽게 합성한다.
    alpha_roi = alpha_roi[:, :, np.newaxis]
    image[image_top:image_bottom, image_left:image_right] = np.clip(
        flame_roi * alpha_roi + roi * (1.0 - alpha_roi),
        0,
        255,
    ).astype(np.uint8)


def main():
    check_input_files()

    image = read_image(IMAGE_PATH, cv2.IMREAD_COLOR)
    if image is None:
        print(f"얼굴 이미지를 읽을 수 없습니다: {IMAGE_PATH.name}")
        raise SystemExit(1)

    flame = read_image(FLAME_PATH, cv2.IMREAD_UNCHANGED)
    if flame is None:
        print(f"불꽃 이미지를 읽을 수 없습니다: {FLAME_PATH.name}")
        raise SystemExit(1)

    flame_bgr, flame_alpha = make_flame_alpha(flame)

    height, width = image.shape[:2]
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_buffer=MODEL_PATH.read_bytes()),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp_image)

    if not result.face_landmarks:
        print("얼굴을 찾지 못했습니다.")
        raise SystemExit(1)

    landmarks = result.face_landmarks[0]
    if len(landmarks) < 478:
        print(f"홍채 랜드마크가 부족합니다: {len(landmarks)}개")
        raise SystemExit(1)

    for iris_indices in IRIS_GROUPS:
        center, diameter = get_iris_center_and_diameter(
            landmarks,
            iris_indices,
            width,
            height,
        )
        overlay_flame(image, flame_bgr, flame_alpha, center, diameter)

    if not write_image(OUTPUT_PATH, image):
        print(f"결과 파일을 저장하지 못했습니다: {OUTPUT_PATH.name}")
        raise SystemExit(1)

    print("눈동자 2개 검출 및 불꽃 합성: 성공")
    print(f"결과 저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
