from datetime import datetime
from pathlib import Path
import time

import pandas as pd
import streamlit as st

from measure import ResourceLogger


BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "static" / "data.csv"
LOG_PATH = BASE_DIR / "logs" / "resource_log.csv"


def load_data_without_cache():
    """캐시 없이 CSV 파일을 읽습니다."""
    return pd.read_csv(CSV_PATH)


@st.cache_data
def load_data_with_cache(file_mtime_ns):
    """캐시를 사용해 CSV 파일을 읽습니다."""
    return pd.read_csv(CSV_PATH)


def load_data():
    """선택한 방식으로 CSV를 읽고 읽기 시간을 기록합니다."""
    # URL에 cache=off를 붙이면 캐시 없이 읽습니다.
    mode = st.query_params.get("cache", "on").lower()
    use_cache = mode not in {"off", "false", "0", "no"}
    lib_name = "streamlit_cache" if use_cache else "streamlit_no_cache"

    start = time.perf_counter()
    with ResourceLogger(LOG_PATH) as logger:
        if use_cache:
            # 파일이 바뀌면 수정 시각이 달라져 캐시가 새로 만들어집니다.
            data = logger.measure(
                lambda: load_data_with_cache(CSV_PATH.stat().st_mtime_ns),
                target="data.csv",
                action="read",
                lib=lib_name,
            )
        else:
            data = logger.measure(
                load_data_without_cache,
                target="data.csv",
                action="read",
                lib=lib_name,
            )

        logger.rows[-1].update(
            rows=len(data),
            file_size=CSV_PATH.stat().st_size,
        )

    elapsed = time.perf_counter() - start
    return data, elapsed


st.set_page_config(page_title="장비 점검 현황", page_icon="🛠️")
st.title("장비 점검 현황 (동적)")

# 버튼을 누르면 서버를 다시 시작하지 않고 앱 코드만 다시 실행합니다.
if st.button("데이터 새로고침"):
    st.rerun()

data, load_elapsed = load_data()
statuses = ["전체"] + sorted(data["status"].dropna().unique().tolist())
selected_status = st.selectbox("상태로 필터링", statuses)

if selected_status == "전체":
    filtered_data = data
else:
    filtered_data = data[data["status"] == selected_status]

display_data = filtered_data.rename(
    columns={
        "name": "장비명",
        "status": "상태",
        "checked_at": "마지막 점검일",
        "cpu": "CPU 사용률(%)",
        "mem": "메모리 사용률(%)",
    }
)

st.caption(f"현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption(f"읽는 데 걸린 시간: {load_elapsed:.4f}초")
st.metric("조회 건수", f"{len(filtered_data)}건")
st.dataframe(display_data, use_container_width=True, hide_index=True)
