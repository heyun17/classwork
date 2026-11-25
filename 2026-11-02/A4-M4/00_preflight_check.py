# ====================================================================
# 파일 용도: Part 1 실행 전에 파일, .env, Python 패키지, OpenSearch 연결,
# sales 인덱스 상태를 한 번에 점검합니다. OpenAI API 호출은 하지 않습니다.
# ====================================================================

import importlib
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def check(label, ok, detail=""):
    mark = "OK" if ok else "확인 필요"
    print(f"[{mark}] {label}", detail)


print("=== Part 1 사전 점검 ===")

# 필수 파일
required_files = [
    "config.py",
    "clients.py",
    "sales_service.py",
    "faiss_service.py",
    "rag_service.py",
    "opensearch_dashboard_sample_100.csv",
    "지역_시장현황_RAG_테스트.md",
]

for name in required_files:
    p = BASE_DIR / name
    check(name, p.exists(), str(p))

# 환경변수
check(
    "OPENAI_API_KEY",
    bool(os.getenv("OPENAI_API_KEY")),
    "값은 화면에 출력하지 않습니다."
)

check(
    "OPENSEARCH_PASSWORD",
    bool(os.getenv("OPENSEARCH_PASSWORD")),
    "값은 화면에 출력하지 않습니다."
)

# 패키지
packages = {
    "pandas": "pandas",
    "numpy": "numpy",
    "faiss": "faiss-cpu",
    "openai": "openai",
    "opensearchpy": "opensearch-py",
    "streamlit": "streamlit",
}

for module_name, install_name in packages.items():
    try:
        importlib.import_module(module_name)
        check(f"패키지 {install_name}", True)
    except Exception as e:
        check(
            f"패키지 {install_name}",
            False,
            f"pip install {install_name}"
        )

# OpenSearch 연결
try:
    from clients import get_opensearch_client

    os_client = get_opensearch_client()
    info = os_client.info()

    check(
        "OpenSearch 연결",
        True,
        f'version={info.get("version", {}).get("number")}'
    )

    exists = os_client.indices.exists(index="sales")
    check("sales 인덱스", bool(exists))

    if exists:
        count = os_client.count(index="sales")["count"]
        check(
            "sales 문서 수",
            count == 100,
            f"count={count}"
        )

except Exception as e:
    check(
        "OpenSearch 연결",
        False,
        str(e)
    )

# FAISS 저장파일은 Step 06 전에는 없어도 정상
faiss_index = BASE_DIR / "rag_faiss" / "index.faiss"
chunks_json = BASE_DIR / "rag_faiss" / "chunks.json"

if faiss_index.exists() and chunks_json.exists():
    check("FAISS 저장파일", True)
else:
    print(
        "[안내] rag_faiss/index.faiss와 chunks.json은 "
        "06_make_faiss.py 실행 후 생성됩니다."
    )
