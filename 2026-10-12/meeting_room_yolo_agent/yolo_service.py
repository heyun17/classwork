from collections import Counter
from pathlib import Path

import cv2
from ultralytics import YOLO

from config import (
    YOLO_MODEL,
    YOLO_CONF,
    IMAGE_DIR,
    OUTPUT_DIR,
    SMALL_GROUP_MAX,
)


class MeetingRoomDetector:
    """YOLO로 회의실 이미지를 분석하는 서비스."""

    def __init__(self) -> None:
        # 모델은 객체 생성 시 한 번만 로드한다.
        self.model = YOLO(YOLO_MODEL)

    @staticmethod
    def _is_allowed_image(image_path: Path) -> bool:
        """meeting_rooms 폴더 내부 파일인지 검사한다."""
        image_path = image_path.resolve()
        image_root = IMAGE_DIR.resolve()
        return image_path.is_relative_to(image_root)

    @staticmethod
    def get_room_state(person_count: int) -> tuple[str, str]:
        """사람 수를 Python 규칙으로 상태로 변환한다."""
        if person_count == 0:
            return "비어있음", "🟢"

        if person_count <= SMALL_GROUP_MAX:
            return "소규모", "🟡"

        return "혼잡", "🔴"

    def analyze_image(self, image_path: Path) -> dict:
        """이미지 하나를 YOLO로 분석하고 Bounding Box 이미지를 저장한다."""
        image_path = image_path.resolve()

        # Guardrail: 허용 폴더 밖의 파일은 분석하지 않는다.
        if not self._is_allowed_image(image_path):
            raise ValueError("허용된 이미지 폴더 밖의 파일입니다.")

        if not image_path.exists():
            raise FileNotFoundError(f"이미지가 없습니다: {image_path}")

        results = self.model.predict(
            source=str(image_path),
            conf=YOLO_CONF,
            verbose=False,
        )

        result = results[0]

        detected_objects: list[dict] = []
        person_count = 0

        for box in result.boxes:
            cls_id = int(box.cls.item())
            cls_name = self.model.names[cls_id]
            confidence = round(float(box.conf.item()), 2)
            xyxy = [round(value, 1) for value in box.xyxy[0].tolist()]

            detected_objects.append(
                {
                    "class": cls_name,
                    "confidence": confidence,
                    "box": xyxy,
                }
            )

            if cls_name == "person":
                person_count += 1

        object_counts = Counter(
            obj["class"] for obj in detected_objects
        )

        state, emoji = self.get_room_state(person_count)

        plot_image = result.plot()
        output_path = OUTPUT_DIR / f"detected_{image_path.name}"

        if not cv2.imwrite(str(output_path), plot_image):
            raise RuntimeError(f"결과 이미지 저장 실패: {output_path}")

        return {
            "file": image_path.name,
            "person_count": person_count,
            "state": state,
            "emoji": emoji,
            "objects": dict(object_counts),
            "detections": detected_objects,
            "result_image": str(output_path),
        }

    def analyze_all(self) -> list[dict]:
        """meeting_rooms 폴더의 모든 지원 이미지를 분석한다."""
        extensions = {".jpg", ".jpeg", ".png", ".webp"}

        images = sorted(
            path
            for path in IMAGE_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in extensions
        )

        if not images:
            raise FileNotFoundError(
                "meeting_rooms 폴더에 분석할 이미지가 없습니다."
            )

        return [self.analyze_image(image) for image in images]
