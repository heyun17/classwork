# A4-M4 미션 7 · Streamlit 상단에 "취소 건수" 추가
# 1) app.py 를 m7_app.py 로 복사
# 2) m7_app.py 에서  c1, c2, c3, c4 = st.columns(4)  를 아래 첫 줄로 바꾸고
# 3) c4.metric(...) 다음 줄에 나머지를 붙여넣기 → 빈칸(______) 채우기
# 4) streamlit run m7_app.py  → 광주 선택 시 3건

c1, c2, c3, c4, c5 = st.columns(5)

canceled = sum(item["doc_count"] for item in summary["status_count"]
               if item["key"] == ______)
c5.metric("취소 건수", f"{canceled}건")
