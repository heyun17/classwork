# ====================================================================
# 파일 용도: A4-M6 공통 설정 — 경로, K 후보, Hybrid 가중치, 청킹 파라미터
# 값을 바꿔도 Vector DB를 다시 만들 필요가 없는 것: K, 가중치 (CLAUDE.md 재실행 규칙)
# ====================================================================
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent      # 프로젝트 폴더 (src의 한 단계 위)
load_dotenv(BASE_DIR / ".env")

DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(exist_ok=True)

METADATA_CSV = DATA_DIR / "metadata.csv"
GOLDEN_JSON = DATA_DIR / "golden_dataset.json"

CHUNK_METHODS = ["heading", "fixed_300", "fixed_500_overlap_100"]
DEFAULT_CHUNK_METHOD = "heading"

K_LIST = [1, 2, 3, 5, 10]
DEFAULT_K = 3

HYBRID_WEIGHTS = {"bm25": 0.4, "vector": 0.6}

EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# openai: 실제 임베딩 / fake: API 키 없이 코드 흐름만 확인 (검색 품질은 의미 없음)
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "openai")

META_FIELDS = ["year", "region", "customer_type", "product", "doc_type", "product_code"]
