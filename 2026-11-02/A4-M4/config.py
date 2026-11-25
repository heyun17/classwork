# ====================================================================
# 파일 용도: 프로젝트 공통 설정(.env, 모델명, 파일 경로, OpenSearch 접속 정보)을 관리합니다.
# ====================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# 같은 폴더의 .env 읽기
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"

SALES_INDEX = "sales"

GPT_MODEL = "gpt-6-luna"
EMBEDDING_MODEL = "text-embedding-3-small"

CSV_PATH = BASE_DIR / "opensearch_dashboard_sample_100.csv"
MD_PATH = BASE_DIR / "지역_시장현황_RAG_테스트.md"

FAISS_DIR = BASE_DIR / "rag_faiss"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
CHUNKS_PATH = FAISS_DIR / "chunks.json"
