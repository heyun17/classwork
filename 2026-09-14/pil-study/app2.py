import streamlit as st
from PIL import Image, ImageEnhance

st.title("간단 이미지 편집기")

uploaded_file = st.file_uploader(
    "이미지 업로드",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    img = Image.open(uploaded_file)

    # 왼쪽 메뉴
    menu = st.sidebar.selectbox(
        "편집 메뉴",
        ["원본", "밝기 조절", "크기 조절", "흑백"]
    )

    # 원본
    if menu == "원본":
        st.image(img)

    # 밝기
    elif menu == "밝기 조절":
        brightness = st.sidebar.slider(
            "밝기",
            0.1, 2.0, 1.0
        )

        enhancer = ImageEnhance.Brightness(img)
        result = enhancer.enhance(brightness)

        st.image(result)

    # 크기
    elif menu == "크기 조절":
        size = st.sidebar.selectbox(
            "크기",
            ["원본", "50%", "25%"]
        )

        if size == "50%":
            result = img.resize(
                (img.width // 2, img.height // 2)
            )

        elif size == "25%":
            result = img.resize(
                (img.width // 4, img.height // 4)
            )

        else:
            result = img

        st.image(result)

    # 흑백
    elif menu == "흑백":
        result = img.convert("L")
        st.image(result)