# ====================================================================
# 파일 용도: OpenAI와 OpenSearch 클라이언트 연결 객체를 생성합니다.
# ====================================================================

from openai import OpenAI
from opensearchpy import OpenSearch

from config import (
    OPENAI_API_KEY,
    OPENSEARCH_PASSWORD,
    OPENSEARCH_HOST,
    OPENSEARCH_PORT,
    OPENSEARCH_USER,
)

def get_openai_client():
    if not OPENAI_API_KEY:
        raise ValueError(".env의 OPENAI_API_KEY를 확인하세요.")

    return OpenAI(
        api_key=OPENAI_API_KEY
    )

def get_opensearch_client():
    if not OPENSEARCH_PASSWORD:
        raise ValueError(".env의 OPENSEARCH_PASSWORD를 확인하세요.")

    return OpenSearch(
        hosts=[
            {
                "host": OPENSEARCH_HOST,
                "port": OPENSEARCH_PORT
            }
        ],
        http_auth=(
            OPENSEARCH_USER,
            OPENSEARCH_PASSWORD
        ),
        use_ssl=True,
        verify_certs=False
    )
