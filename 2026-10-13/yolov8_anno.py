import cv2
import numpy as np
from pathlib import Path


# ============================================================
# 설정
# ============================================================

IMAGE_DIR = Path("images")
LABEL_DIR = Path("labels")

CLASSES = [
    "helmet",
    "no_helmet",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

# UI 크기
VIEW_WIDTH = 760
VIEW_HEIGHT = 600
PANEL_WIDTH = 300

WINDOW_WIDTH = VIEW_WIDTH + PANEL_WIDTH
WINDOW_HEIGHT = VIEW_HEIGHT


# 클래스별 Bounding Box 색상
CLASS_COLORS = [
    (0, 255, 0),      # helmet
    (0, 100, 255),    # no_helmet
]


# ============================================================
# 데이터 준비
# ============================================================

LABEL_DIR.mkdir(parents=True, exist_ok=True)

if not IMAGE_DIR.exists():
    raise FileNotFoundError(
        f"images 폴더가 없습니다.\n"
        f"현재 찾는 위치: {IMAGE_DIR.resolve()}"
    )

images = sorted(
    p for p in IMAGE_DIR.iterdir()
    if p.suffix.lower() in IMAGE_EXTENSIONS
)

if not images:
    raise FileNotFoundError(
        f"{IMAGE_DIR.resolve()} 안에 이미지가 없습니다."
    )


# ============================================================
# 상태값
# ============================================================

current_index = 0
current_class = 0

image = None

boxes = []

drawing = False

start_x = 0
start_y = 0

mouse_x = 0
mouse_y = 0

display_scale = 1.0
display_width = 0
display_height = 0

offset_x = 0
offset_y = 0

buttons = []


# ============================================================
# 라벨 불러오기
# ============================================================

def load_labels(image_path, image_width, image_height):

    label_path = LABEL_DIR / f"{image_path.stem}.txt"

    loaded_boxes = []

    if not label_path.exists():
        return loaded_boxes

    with open(label_path, "r", encoding="utf-8") as f:

        for line in f:

            parts = line.strip().split()

            if len(parts) != 5:
                continue

            class_id = int(parts[0])

            x_center = float(parts[1])
            y_center = float(parts[2])

            box_width = float(parts[3])
            box_height = float(parts[4])

            x1 = int(
                (x_center - box_width / 2)
                * image_width
            )

            y1 = int(
                (y_center - box_height / 2)
                * image_height
            )

            x2 = int(
                (x_center + box_width / 2)
                * image_width
            )

            y2 = int(
                (y_center + box_height / 2)
                * image_height
            )

            loaded_boxes.append(
                (
                    class_id,
                    x1,
                    y1,
                    x2,
                    y2
                )
            )

    return loaded_boxes


# ============================================================
# YOLO 라벨 저장
# ============================================================

def save_labels():

    if image is None:
        return

    image_height, image_width = image.shape[:2]

    image_path = images[current_index]

    label_path = (
        LABEL_DIR
        / f"{image_path.stem}.txt"
    )

    with open(
        label_path,
        "w",
        encoding="utf-8"
    ) as f:

        for (
            class_id,
            x1,
            y1,
            x2,
            y2
        ) in boxes:

            x_center = (
                (x1 + x2) / 2
            ) / image_width

            y_center = (
                (y1 + y2) / 2
            ) / image_height

            box_width = (
                abs(x2 - x1)
            ) / image_width

            box_height = (
                abs(y2 - y1)
            ) / image_height

            f.write(
                f"{class_id} "
                f"{x_center:.6f} "
                f"{y_center:.6f} "
                f"{box_width:.6f} "
                f"{box_height:.6f}\n"
            )

    print("Saved:", label_path)


# ============================================================
# 이미지 불러오기
# ============================================================

def load_image():

    global image
    global boxes

    global display_scale
    global display_width
    global display_height

    global offset_x
    global offset_y

    image_path = images[current_index]

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        raise ValueError(
            f"이미지를 읽을 수 없습니다: "
            f"{image_path}"
        )

    height, width = image.shape[:2]

    # 이미지가 VIEW 영역 안에 들어오도록 축소
    display_scale = min(
        VIEW_WIDTH / width,
        VIEW_HEIGHT / height,
        1.0
    )

    display_width = int(
        width * display_scale
    )

    display_height = int(
        height * display_scale
    )

    # 가운데 정렬
    offset_x = (
        VIEW_WIDTH - display_width
    ) // 2

    offset_y = (
        VIEW_HEIGHT - display_height
    ) // 2

    boxes = load_labels(
        image_path,
        width,
        height
    )


# ============================================================
# 좌표 변환
# ============================================================

def original_to_screen(x, y):

    screen_x = int(
        offset_x
        + x * display_scale
    )

    screen_y = int(
        offset_y
        + y * display_scale
    )

    return screen_x, screen_y


def screen_to_original(x, y):

    height, width = image.shape[:2]

    x = max(
        offset_x,
        min(
            x,
            offset_x + display_width - 1
        )
    )

    y = max(
        offset_y,
        min(
            y,
            offset_y + display_height - 1
        )
    )

    original_x = int(
        (x - offset_x)
        / display_scale
    )

    original_y = int(
        (y - offset_y)
        / display_scale
    )

    original_x = max(
        0,
        min(
            original_x,
            width - 1
        )
    )

    original_y = max(
        0,
        min(
            original_y,
            height - 1
        )
    )

    return original_x, original_y


def mouse_inside_image(x, y):

    return (
        offset_x <= x <
        offset_x + display_width
        and
        offset_y <= y <
        offset_y + display_height
    )


# ============================================================
# 버튼
# ============================================================

def draw_button(
    canvas,
    text,
    x,
    y,
    width,
    height,
    action,
    selected=False,
    danger=False
):

    if selected:
        bg = (0, 170, 0)

    elif danger:
        bg = (70, 70, 180)

    else:
        bg = (70, 70, 70)

    cv2.rectangle(
        canvas,
        (x, y),
        (
            x + width,
            y + height
        ),
        bg,
        -1
    )

    cv2.rectangle(
        canvas,
        (x, y),
        (
            x + width,
            y + height
        ),
        (180, 180, 180),
        1
    )

    cv2.putText(
        canvas,
        text,
        (
            x + 12,
            y + int(height * 0.68)
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    buttons.append(
        {
            "rect": (
                x,
                y,
                x + width,
                y + height
            ),
            "action": action
        }
    )


# ============================================================
# 화면 그리기
# ============================================================

def redraw():

    global buttons

    buttons = []

    # 전체 프로그램 배경
    canvas = np.full(
        (
            WINDOW_HEIGHT,
            WINDOW_WIDTH,
            3
        ),
        30,
        dtype=np.uint8
    )

    # --------------------------------------------------------
    # 이미지 표시
    # --------------------------------------------------------

    resized = cv2.resize(
        image,
        (
            display_width,
            display_height
        )
    )

    canvas[
        offset_y:
        offset_y + display_height,

        offset_x:
        offset_x + display_width
    ] = resized


    # --------------------------------------------------------
    # 저장된 Bounding Box
    # --------------------------------------------------------

    for (
        class_id,
        x1,
        y1,
        x2,
        y2
    ) in boxes:

        sx1, sy1 = original_to_screen(
            x1,
            y1
        )

        sx2, sy2 = original_to_screen(
            x2,
            y2
        )

        color = CLASS_COLORS[
            class_id % len(CLASS_COLORS)
        ]

        cv2.rectangle(
            canvas,
            (sx1, sy1),
            (sx2, sy2),
            color,
            2
        )

        label = CLASSES[class_id]

        # 라벨 배경
        text_size, _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            2
        )

        label_y = max(
            sy1,
            22
        )

        cv2.rectangle(
            canvas,
            (
                sx1,
                label_y - 22
            ),
            (
                sx1 + text_size[0] + 8,
                label_y
            ),
            color,
            -1
        )

        cv2.putText(
            canvas,
            label,
            (
                sx1 + 4,
                label_y - 5
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            2,
            cv2.LINE_AA
        )


    # --------------------------------------------------------
    # 현재 그리는 박스
    # --------------------------------------------------------

    if drawing:

        sx1, sy1 = original_to_screen(
            start_x,
            start_y
        )

        sx2, sy2 = original_to_screen(
            mouse_x,
            mouse_y
        )

        cv2.rectangle(
            canvas,
            (sx1, sy1),
            (sx2, sy2),
            (0, 255, 255),
            2
        )


    # ========================================================
    # 오른쪽 패널
    # ========================================================

    panel_x = VIEW_WIDTH

    cv2.rectangle(
        canvas,
        (
            panel_x,
            0
        ),
        (
            WINDOW_WIDTH,
            WINDOW_HEIGHT
        ),
        (45, 45, 45),
        -1
    )


    # --------------------------------------------------------
    # 제목
    # --------------------------------------------------------

    cv2.putText(
        canvas,
        "YOLO Annotation Tool",
        (
            panel_x + 18,
            35
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )


    # 현재 이미지
    cv2.putText(
        canvas,
        f"Image {current_index + 1} / {len(images)}",
        (
            panel_x + 18,
            67
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (220, 220, 220),
        1,
        cv2.LINE_AA
    )


    file_name = images[current_index].name

    if len(file_name) > 31:
        file_name = (
            file_name[:28] + "..."
        )

    cv2.putText(
        canvas,
        file_name,
        (
            panel_x + 18,
            91
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (180, 180, 180),
        1,
        cv2.LINE_AA
    )


    # --------------------------------------------------------
    # 클래스 선택
    # --------------------------------------------------------

    cv2.putText(
        canvas,
        "1. Select class",
        (
            panel_x + 18,
            125
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    y = 140

    for class_id, class_name in enumerate(
        CLASSES
    ):

        draw_button(
            canvas,
            f"{class_id}: {class_name}",
            panel_x + 18,
            y,
            264,
            38,
            (
                "class",
                class_id
            ),
            selected=(
                current_class
                == class_id
            )
        )

        y += 45


    # --------------------------------------------------------
    # 사용 안내
    # --------------------------------------------------------

    y += 12

    cv2.putText(
        canvas,
        "2. Draw bounding box",
        (
            panel_x + 18,
            y
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    y += 25

    cv2.putText(
        canvas,
        "Left mouse drag on image",
        (
            panel_x + 18,
            y
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (190, 190, 190),
        1,
        cv2.LINE_AA
    )


    # --------------------------------------------------------
    # 조작 버튼
    # --------------------------------------------------------

    y += 35

    draw_button(
        canvas,
        "Save",
        panel_x + 18,
        y,
        125,
        42,
        "save"
    )

    draw_button(
        canvas,
        "Undo",
        panel_x + 157,
        y,
        125,
        42,
        "undo"
    )


    y += 52

    draw_button(
        canvas,
        "Previous",
        panel_x + 18,
        y,
        125,
        42,
        "previous"
    )

    draw_button(
        canvas,
        "Next",
        panel_x + 157,
        y,
        125,
        42,
        "next"
    )


    y += 52

    draw_button(
        canvas,
        "Clear All",
        panel_x + 18,
        y,
        264,
        42,
        "clear"
    )


    y += 52

    draw_button(
        canvas,
        "Save && Exit",
        panel_x + 18,
        y,
        264,
        42,
        "exit",
        danger=True
    )


    # --------------------------------------------------------
    # 상태 표시
    # --------------------------------------------------------

    y += 58

    cv2.putText(
        canvas,
        f"Boxes: {len(boxes)}",
        (
            panel_x + 18,
            y
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (220, 220, 220),
        1,
        cv2.LINE_AA
    )

    y += 25

    cv2.putText(
        canvas,
        f"Selected: {CLASSES[current_class]}",
        (
            panel_x + 18,
            y
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        CLASS_COLORS[
            current_class
            % len(CLASS_COLORS)
        ],
        2,
        cv2.LINE_AA
    )


    cv2.imshow(
        "YOLO Annotation",
        canvas
    )


# ============================================================
# 버튼 실행
# ============================================================

def handle_action(action):

    global current_class
    global current_index
    global boxes

    if isinstance(
        action,
        tuple
    ):

        if action[0] == "class":

            current_class = action[1]

            redraw()

        return False


    if action == "save":

        save_labels()
        redraw()


    elif action == "undo":

        if boxes:
            boxes.pop()

        redraw()


    elif action == "clear":

        boxes.clear()
        redraw()


    elif action == "previous":

        save_labels()

        if current_index > 0:

            current_index -= 1

            load_image()

        redraw()


    elif action == "next":

        save_labels()

        if current_index < len(images) - 1:

            current_index += 1

            load_image()

        redraw()


    elif action == "exit":

        save_labels()

        return True


    return False


# ============================================================
# 마우스 이벤트
# ============================================================

def mouse_callback(
    event,
    x,
    y,
    flags,
    param
):

    global drawing

    global start_x
    global start_y

    global mouse_x
    global mouse_y


    # --------------------------------------------------------
    # 패널 클릭
    # --------------------------------------------------------

    if (
        event == cv2.EVENT_LBUTTONDOWN
        and
        x >= VIEW_WIDTH
    ):

        for button in buttons:

            x1, y1, x2, y2 = (
                button["rect"]
            )

            if (
                x1 <= x <= x2
                and
                y1 <= y <= y2
            ):

                exit_requested = (
                    handle_action(
                        button["action"]
                    )
                )

                if exit_requested:

                    cv2.destroyAllWindows()

                    raise SystemExit

                return


    # --------------------------------------------------------
    # 박스 그리기 시작
    # --------------------------------------------------------

    if (
        event == cv2.EVENT_LBUTTONDOWN
        and
        mouse_inside_image(
            x,
            y
        )
    ):

        drawing = True

        start_x, start_y = (
            screen_to_original(
                x,
                y
            )
        )

        mouse_x = start_x
        mouse_y = start_y

        redraw()


    # --------------------------------------------------------
    # 드래그 중
    # --------------------------------------------------------

    elif (
        event == cv2.EVENT_MOUSEMOVE
        and
        drawing
    ):

        mouse_x, mouse_y = (
            screen_to_original(
                x,
                y
            )
        )

        redraw()


    # --------------------------------------------------------
    # 박스 완성
    # --------------------------------------------------------

    elif (
        event == cv2.EVENT_LBUTTONUP
        and
        drawing
    ):

        drawing = False

        end_x, end_y = (
            screen_to_original(
                x,
                y
            )
        )

        x1 = min(
            start_x,
            end_x
        )

        y1 = min(
            start_y,
            end_y
        )

        x2 = max(
            start_x,
            end_x
        )

        y2 = max(
            start_y,
            end_y
        )

        # 실수로 클릭만 한 경우 제외
        if (
            x2 - x1 >= 5
            and
            y2 - y1 >= 5
        ):

            boxes.append(
                (
                    current_class,
                    x1,
                    y1,
                    x2,
                    y2
                )
            )

        redraw()


# ============================================================
# 실행
# ============================================================

load_image()

cv2.namedWindow(
    "YOLO Annotation",
    cv2.WINDOW_AUTOSIZE
)

cv2.setMouseCallback(
    "YOLO Annotation",
    mouse_callback
)

redraw()


while True:

    key = cv2.waitKey(20) & 0xFF

    # ESC 비상 종료
    if key == 27:

        save_labels()

        break


cv2.destroyAllWindows()