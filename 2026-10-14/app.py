# ============================================================
# Streamlit 실시간 사람 세그멘테이션 + 프레임 캡처
# + RGB 히스토그램 분석
# + OpenAI GPT 분석 / 질의응답
# ============================================================

import os
import json
import base64
import threading
from pathlib import Path
from datetime import datetime

import av
import cv2
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import torch

from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

from torchvision.models.segmentation import (
    deeplabv3_resnet50,
    DeepLabV3_ResNet50_Weights,
)

from streamlit_webrtc import webrtc_streamer
from streamlit_shortcuts import shortcut_button


# ============================================================
# 1. 기본 경로 설정
# ============================================================

# 현재 app.py가 있는 폴더
BASE_DIR = Path(__file__).resolve().parent

# 배경 이미지 위치
BACK_PATH = BASE_DIR / "back.jpg"

# 캡처한 이미지를 저장할 폴더
CAPTURE_DIR = BASE_DIR / "captures"

# 폴더가 없으면 자동 생성
CAPTURE_DIR.mkdir(exist_ok=True)


# ============================================================
# 2. .env 파일 읽기
# ============================================================

load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# .env에서 모델 이름을 지정하지 않았다면 기본값 사용
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-6-luna"
)


# ============================================================
# 3. Streamlit 페이지 기본 설정
# ============================================================

st.set_page_config(
    page_title="Person Segmentation Analyzer",
    layout="wide",
)

st.title("실시간 사람 세그멘테이션 & 이미지 분석")


# ============================================================
# 4. PyTorch 모델 불러오기
#
# @st.cache_resource를 사용하면
# Streamlit이 화면을 다시 그릴 때마다
# 모델을 계속 다시 불러오지 않는다.
# ============================================================

@st.cache_resource
def load_segmentation_model():

    # GPU가 있으면 CUDA 사용
    # 없으면 CPU 사용
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    # DeepLabV3 사전학습 가중치
    weights = DeepLabV3_ResNet50_Weights.DEFAULT

    # 모델 생성
    model = deeplabv3_resnet50(
        weights=weights
    )

    # 모델을 CPU/GPU로 이동
    model = model.to(device)

    # 추론 모드
    model.eval()

    # 모델에서 요구하는 전처리 함수
    preprocess = weights.transforms()

    # VOC 클래스 목록
    categories = weights.meta["categories"]

    # person 클래스 번호
    person_class = categories.index("person")

    return (
        model,
        preprocess,
        person_class,
        device,
    )


model, preprocess, person_class, device = (
    load_segmentation_model()
)

st.caption(
    f"PyTorch 실행 장치: {device}"
)


# ============================================================
# 5. back.jpg 불러오기
# ============================================================

@st.cache_data
def load_background(path: str):

    background = cv2.imread(path)

    if background is None:
        raise FileNotFoundError(
            f"배경 이미지를 찾을 수 없습니다: {path}"
        )

    return background


background = load_background(
    str(BACK_PATH)
)


# ============================================================
# 6. 실시간 영상 프레임 공유용 클래스
#
# WebRTC 영상 처리는 별도 thread에서 실행된다.
#
# Streamlit 버튼을 누르는 부분과
# 영상 처리 부분이 동시에 같은 데이터를 접근할 수 있기 때문에
# threading.Lock을 사용한다.
# ============================================================

class FrameStore:

    def __init__(self):

        # 가장 최근의 합성 결과 프레임
        self.frame = None

        # thread 충돌 방지
        self.lock = threading.Lock()


# Streamlit이 rerun되어도 프레임 저장소가 유지되도록
# session_state에 저장
if "frame_store" not in st.session_state:
    st.session_state.frame_store = FrameStore()


frame_store = st.session_state.frame_store


# ============================================================
# 7. 사람 세그멘테이션 함수
# ============================================================

def segment_person(frame):

    # frame은 OpenCV 형식
    # shape = [height, width, 3]
    height, width = frame.shape[:2]


    # --------------------------------------------------------
    # OpenCV BGR → RGB
    # --------------------------------------------------------

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    # --------------------------------------------------------
    # NumPy → PIL
    # --------------------------------------------------------

    pil_image = Image.fromarray(
        rgb_frame
    )


    # --------------------------------------------------------
    # DeepLabV3 입력 전처리
    #
    # [C, H, W]
    # →
    # [1, C, H, W]
    # --------------------------------------------------------

    input_tensor = preprocess(
        pil_image
    ).unsqueeze(0)

    input_tensor = input_tensor.to(
        device
    )


    # --------------------------------------------------------
    # AI 모델 추론
    # --------------------------------------------------------

    with torch.inference_mode():

        output = model(
            input_tensor
        )["out"][0]


    # --------------------------------------------------------
    # 각 픽셀에서 가장 확률 높은 클래스 선택
    # --------------------------------------------------------

    prediction = output.argmax(
        0
    ).cpu().numpy()


    # --------------------------------------------------------
    # person인 픽셀만 1
    # 나머지는 0
    # --------------------------------------------------------

    person_mask = (
        prediction == person_class
    ).astype(np.uint8)


    # --------------------------------------------------------
    # 모델 출력 mask를
    # 원래 웹캠 영상 크기로 변경
    # --------------------------------------------------------

    person_mask = cv2.resize(
        person_mask,
        (width, height),
        interpolation=cv2.INTER_NEAREST,
    )


    # --------------------------------------------------------
    # 배경 이미지도 웹캠 크기로 변경
    # --------------------------------------------------------

    back_resized = cv2.resize(
        background,
        (width, height),
    )


    # --------------------------------------------------------
    # mask를 3차원으로 변경
    #
    # [H, W]
    # →
    # [H, W, 1]
    # --------------------------------------------------------

    mask = person_mask[:, :, np.newaxis]


    # --------------------------------------------------------
    # 최종 합성
    #
    # 사람 영역:
    #     원래 웹캠
    #
    # 사람 이외:
    #     back.jpg
    # --------------------------------------------------------

    result = (
        frame * mask
        +
        back_resized * (1 - mask)
    )


    return result.astype(
        np.uint8
    )


# ============================================================
# 8. WebRTC에서 각 영상 프레임을 처리하는 callback
# ============================================================

def video_frame_callback(frame):

    # WebRTC VideoFrame
    # →
    # OpenCV BGR NumPy 배열
    image = frame.to_ndarray(
        format="bgr24"
    )


    # 사람 세그멘테이션 + 배경 합성
    result = segment_person(
        image
    )


    # --------------------------------------------------------
    # 가장 최근 프레임을 FrameStore에 보관
    #
    # 사용자가 S 키를 누르면
    # 여기 저장되어 있는 프레임을 가져간다.
    # --------------------------------------------------------

    with frame_store.lock:

        frame_store.frame = (
            result.copy()
        )


    # --------------------------------------------------------
    # 합성 결과를 다시 WebRTC VideoFrame으로 변환
    # --------------------------------------------------------

    return av.VideoFrame.from_ndarray(
        result,
        format="bgr24",
    )


# ============================================================
# 9. RGB 히스토그램 분석
# ============================================================

def analyze_histogram(frame):

    # OpenCV BGR → RGB
    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # 밝기 분석용 grayscale
    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    # GPT에게 전달할 결과
    result = {
        "channels": {}
    }


    # --------------------------------------------------------
    # RGB 각 채널 분석
    # --------------------------------------------------------

    channel_names = [
        "Red",
        "Green",
        "Blue",
    ]

    for index, name in enumerate(
        channel_names
    ):

        channel = rgb[:, :, index]


        # 256단계 histogram 계산
        hist = cv2.calcHist(
            [rgb],
            [index],
            None,
            [256],
            [0, 256],
        ).flatten()


        # ----------------------------------------------------
        # GPT에 256개 값을 모두 보내지 않고
        # 16구간으로 요약한다.
        #
        # 0~15
        # 16~31
        # ...
        # 240~255
        # ----------------------------------------------------

        hist16 = hist.reshape(
            16,
            16
        ).sum()


        # 전체 픽셀 대비 비율(%)
        hist16_percent = (
            hist16
            / hist16.sum()
            * 100
        )


        result["channels"][name] = {

            # 평균 채널 값
            "mean": round(
                float(channel.mean()),
                2,
            ),

            # 표준편차
            "std": round(
                float(channel.std()),
                2,
            ),

            # histogram에서 가장 많이 나온 밝기값
            "peak_intensity": int(
                np.argmax(hist)
            ),

            # 16구간 histogram %
            "histogram_16_bins_percent": [
                round(float(x), 2)
                for x in hist16_percent
            ],
        }


    # --------------------------------------------------------
    # 전체 밝기 분석
    # --------------------------------------------------------

    result["brightness"] = {

        "mean": round(
            float(gray.mean()),
            2,
        ),

        "std": round(
            float(gray.std()),
            2,
        ),

        # 어두운 영역
        "dark_percent": round(
            float(
                np.mean(gray < 85) * 100
            ),
            2,
        ),

        # 중간 밝기
        "middle_percent": round(
            float(
                np.mean(
                    (gray >= 85)
                    & (gray < 170)
                )
                * 100
            ),
            2,
        ),

        # 밝은 영역
        "bright_percent": round(
            float(
                np.mean(gray >= 170)
                * 100
            ),
            2,
        ),
    }

    return result


# ============================================================
# 10. RGB Histogram 그래프 생성
# ============================================================

def create_histogram_figure(frame):

    # BGR → RGB
    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    # 그래프 생성
    fig, ax = plt.subplots(
        figsize=(8, 4)
    )


    channel_info = [

        (0, "Red", "red"),

        (1, "Green", "green"),

        (2, "Blue", "blue"),
    ]


    for index, label, color in channel_info:

        hist = cv2.calcHist(
            [rgb],
            [index],
            None,
            [256],
            [0, 256],
        )

        ax.plot(
            hist,
            label=label,
            color=color,
        )


    ax.set_xlim(
        [0, 256]
    )

    ax.set_xlabel(
        "Pixel intensity"
    )

    ax.set_ylabel(
        "Pixel count"
    )

    ax.set_title(
        "RGB Histogram"
    )

    ax.legend()

    ax.grid(
        alpha=0.2
    )

    fig.tight_layout()

    return fig


# ============================================================
# 11. 프레임 → JPG 저장
# ============================================================

def save_capture(frame):

    # 현재 시간으로 파일 이름 생성
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    filename = (
        CAPTURE_DIR
        / f"capture_{timestamp}.jpg"
    )


    cv2.imwrite(
        str(filename),
        frame,
    )

    return filename


# ============================================================
# 12. OpenAI Client 생성
# ============================================================

def get_openai_client():

    if not OPENAI_API_KEY:

        return None

    return OpenAI(
        api_key=OPENAI_API_KEY
    )


client = get_openai_client()


# ============================================================
# 13. GPT용 histogram 설명 문자열
# ============================================================

def histogram_to_text(
    histogram_data
):

    return json.dumps(
        histogram_data,
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# 14. GPT에게 histogram 자동 요약 요청
# ============================================================

def summarize_histogram(
    histogram_data
):

    if client is None:

        return (
            ".env에 OPENAI_API_KEY가 "
            "설정되어 있지 않습니다."
        )


    histogram_text = histogram_to_text(
        histogram_data
    )


    prompt = f"""
다음은 하나의 이미지에서 계산한 RGB 히스토그램 분석 결과입니다.

{histogram_text}

각 RGB 채널의 값 범위는 0~255입니다.

histogram_16_bins_percent는 다음 구간의 픽셀 비율입니다.

0: 0~15
1: 16~31
2: 32~47
...
15: 240~255

이 자료를 바탕으로 다음을 한국어로 간단히 설명하세요.

1. 전체적인 밝기 특성
2. RGB 색상 분포 특징
3. 대비가 높은지 낮은지
4. 이미지가 전반적으로 밝은지 어두운지
5. 눈에 띄는 histogram 특징

중요:
히스토그램만으로 확인할 수 없는
사람의 신원, 사물 종류, 장소, 브랜드 등은 추측하지 마세요.
"""


    response = client.responses.create(

        model=OPENAI_MODEL,

        input=[
            {
                "role": "developer",
                "content":
                    "당신은 이미지 히스토그램을 "
                    "객관적으로 해석하는 분석 도우미입니다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )


    return response.output_text


# ============================================================
# 15. GPT 질의응답
# ============================================================

def ask_histogram_question(
    question,
    histogram_data,
    summary,
    history,
):

    histogram_text = histogram_to_text(
        histogram_data
    )


    # 기본 context
    messages = [

        {
            "role": "developer",

            "content":
                """
사용자의 질문에
RGB 히스토그램 및 밝기 통계에 근거하여 답하세요.

히스토그램만으로 확인할 수 없는
객체 종류, 사람 신원, 장소 등의 정보를
확정적으로 추측하지 마세요.

알 수 없는 내용은
'히스토그램만으로는 판단할 수 없습니다'
라고 명확히 설명하세요.
""",
        },

        {
            "role": "user",

            "content":
                f"""
현재 이미지의 histogram 데이터:

{histogram_text}

기존 분석 요약:

{summary}
""",
        },
    ]


    # --------------------------------------------------------
    # 기존 채팅 기록 추가
    #
    # 너무 길어지는 것을 막기 위해
    # 최근 6개만 사용
    # --------------------------------------------------------

    for message in history[-6:]:

        messages.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )


    # 이번 질문
    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )


    response = client.responses.create(

        model=OPENAI_MODEL,

        input=messages,
    )


    return response.output_text


# ============================================================
# 16. Streamlit Session State 초기값
# ============================================================

if "captured_frame" not in st.session_state:

    st.session_state.captured_frame = None


if "histogram_data" not in st.session_state:

    st.session_state.histogram_data = None


if "ai_summary" not in st.session_state:

    st.session_state.ai_summary = None


if "chat_history" not in st.session_state:

    st.session_state.chat_history = []


if "capture_path" not in st.session_state:

    st.session_state.capture_path = None


# ============================================================
# 17. 화면 레이아웃
#
# 왼쪽:
#   실시간 웹캠
#
# 오른쪽:
#   S로 찍은 사진
# ============================================================

video_col, capture_col = st.columns(
    [1.4, 1]
)


# ============================================================
# 18. 왼쪽 - 실시간 비디오
# ============================================================

with video_col:

    st.subheader(
        "실시간 영상"
    )

    st.caption(
        "사람은 원본으로 유지하고 "
        "나머지 영역은 back.jpg로 변경합니다."
    )


    # --------------------------------------------------------
    # 브라우저 웹캠 시작
    # --------------------------------------------------------

    webrtc_ctx = webrtc_streamer(

        key="person-segmentation",

        video_frame_callback=(
            video_frame_callback
        ),

        # 카메라만 사용
        # 마이크는 사용하지 않음
        media_stream_constraints={
            "video": True,
            "audio": False,
        },

        # 영상 처리를 비동기로 실행
        async_processing=True,
    )


    # --------------------------------------------------------
    # 버튼 클릭 또는 키보드 S 키로 캡처
    # --------------------------------------------------------

    capture_pressed = shortcut_button(

        "📸 현재 프레임 저장",

        # 키보드 단축키
        "s",

        key="capture_button",

        type="primary",

        use_container_width=True,
    )


    st.caption(
        "버튼을 클릭하거나 키보드 S를 누르면 "
        "현재 프레임을 저장합니다."
    )


# ============================================================
# 19. S 키가 눌렸을 때 현재 frame 저장
# ============================================================

if capture_pressed:

    # --------------------------------------------------------
    # 영상 thread와 충돌하지 않도록
    # lock 안에서 현재 프레임 복사
    # --------------------------------------------------------

    with frame_store.lock:

        if frame_store.frame is not None:

            current_frame = (
                frame_store.frame.copy()
            )

        else:

            current_frame = None


    if current_frame is None:

        st.warning(
            "아직 카메라 프레임이 없습니다. "
            "먼저 카메라를 START 해주세요."
        )

    else:

        # 캡처 이미지 보관
        st.session_state.captured_frame = (
            current_frame
        )


        # 실제 JPG 파일로 저장
        capture_path = save_capture(
            current_frame
        )

        st.session_state.capture_path = (
            str(capture_path)
        )


        # Histogram 계산
        histogram_data = (
            analyze_histogram(
                current_frame
            )
        )

        st.session_state.histogram_data = (
            histogram_data
        )


        # 새로운 이미지이므로
        # 이전 Q&A 기록 초기화
        st.session_state.chat_history = []


        # ----------------------------------------------------
        # GPT 자동 요약
        # ----------------------------------------------------

        if client is not None:

            with st.spinner(
                "GPT가 히스토그램을 분석 중입니다..."
            ):

                try:

                    st.session_state.ai_summary = (
                        summarize_histogram(
                            histogram_data
                        )
                    )

                except Exception as e:

                    st.session_state.ai_summary = (
                        f"GPT API 오류: {e}"
                    )

        else:

            st.session_state.ai_summary = (
                ".env에 OPENAI_API_KEY를 "
                "설정하면 GPT 분석을 사용할 수 있습니다."
            )


# ============================================================
# 20. 오른쪽 - 저장된 이미지 표시
# ============================================================

with capture_col:

    st.subheader(
        "캡처 이미지"
    )


    if st.session_state.captured_frame is None:

        st.info(
            "S 키를 누르면 현재 영상이 여기에 표시됩니다."
        )

    else:

        # OpenCV BGR → Streamlit용 RGB
        captured_rgb = cv2.cvtColor(

            st.session_state.captured_frame,

            cv2.COLOR_BGR2RGB,
        )


        st.image(

            captured_rgb,

            caption="저장된 프레임",

            use_container_width=True,
        )


        st.caption(
            f"저장 위치: "
            f"{st.session_state.capture_path}"
        )


# ============================================================
# 21. Histogram 표시
# ============================================================

if st.session_state.captured_frame is not None:

    st.divider()

    st.header(
        "이미지 Histogram 분석"
    )


    # --------------------------------------------------------
    # RGB Histogram
    # --------------------------------------------------------

    fig = create_histogram_figure(
        st.session_state.captured_frame
    )

    st.pyplot(
        fig,
        use_container_width=True,
    )

    # 메모리에서 figure 제거
    plt.close(fig)


    histogram_data = (
        st.session_state.histogram_data
    )


    # --------------------------------------------------------
    # 주요 통계값 표시
    # --------------------------------------------------------

    red_col, green_col, blue_col, light_col = (
        st.columns(4)
    )


    red_col.metric(

        "Red 평균",

        histogram_data[
            "channels"
        ]["Red"]["mean"],
    )


    green_col.metric(

        "Green 평균",

        histogram_data[
            "channels"
        ]["Green"]["mean"],
    )


    blue_col.metric(

        "Blue 평균",

        histogram_data[
            "channels"
        ]["Blue"]["mean"],
    )


    light_col.metric(

        "평균 밝기",

        histogram_data[
            "brightness"
        ]["mean"],
    )


    # 밝기 비율
    b1, b2, b3 = st.columns(3)


    b1.metric(

        "어두운 영역",

        f"""
        {
            histogram_data[
                "brightness"
            ]["dark_percent"]
        }%
        """,
    )


    b2.metric(

        "중간 밝기",

        f"""
        {
            histogram_data[
                "brightness"
            ]["middle_percent"]
        }%
        """,
    )


    b3.metric(

        "밝은 영역",

        f"""
        {
            histogram_data[
                "brightness"
            ]["bright_percent"]
        }%
        """,
    )


# ============================================================
# 22. GPT Histogram 요약
# ============================================================

if st.session_state.histogram_data is not None:

    st.divider()

    st.header(
        "GPT Histogram 분석"
    )


    if st.session_state.ai_summary:

        st.markdown(
            st.session_state.ai_summary
        )


# ============================================================
# 23. GPT와 histogram 질의응답
# ============================================================

if (
    st.session_state.histogram_data
    is not None
):

    st.divider()

    st.header(
        "Histogram 질의응답"
    )


    # --------------------------------------------------------
    # 기존 대화 출력
    # --------------------------------------------------------

    for message in (
        st.session_state.chat_history
    ):

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    # --------------------------------------------------------
    # API KEY가 있을 때만 질문 입력 활성화
    # --------------------------------------------------------

    if client is None:

        st.warning(
            ".env에 OPENAI_API_KEY를 설정해야 "
            "질의응답을 사용할 수 있습니다."
        )

    else:

        question = st.chat_input(
            "예: 이 이미지는 전반적으로 밝은 편이야?"
        )


        if question:

            # 이전 대화 저장
            old_history = (
                st.session_state
                .chat_history
                .copy()
            )


            # 사용자 질문 저장
            st.session_state.chat_history.append(
                {
                    "role": "user",
                    "content": question,
                }
            )


            with st.chat_message(
                "user"
            ):

                st.markdown(
                    question
                )


            # GPT 답변
            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "분석 중..."
                ):

                    try:

                        answer = (
                            ask_histogram_question(
                                question,
                                st.session_state.histogram_data,
                                st.session_state.ai_summary,
                                old_history,
                            )
                        )

                    except Exception as e:

                        answer = (
                            f"GPT API 오류: {e}"
                        )


                st.markdown(
                    answer
                )


            # GPT 응답도 history에 저장
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )
            