import streamlit as st
from PIL import Image

st.title("이미지 크기 축소")

uploaded_file = st.file_uploader(
    "이미지를 업로드하세요",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    img = Image.open(uploaded_file)

    st.write("원본 이미지")
    st.image(img)

    if st.button("50%로 축소"):
        new_size = (
            img.width // 2,
            img.height // 2
        )
        resized = img.resize(new_size)

        st.write("50% 이미지")
        st.image(resized)

    if st.button("25%로 축소"):
        new_size = (
            img.width // 4,
            img.height // 4
        )
        resized = img.resize(new_size)

        st.write("25% 이미지")
        st.image(resized)