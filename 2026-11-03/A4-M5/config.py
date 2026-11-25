import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent
load_dotenv(BASE_DIR/".env")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
OPENSEARCH_PASSWORD=os.getenv("OPENSEARCH_PASSWORD")
RAG_INDEX="rag_docs"
SALES_INDEX="sales"
EMBEDDING_MODEL="text-embedding-3-small"
GPT_MODEL="gpt-6-luna"
FAISS_INDEX_PATH=BASE_DIR/"rag_faiss"/"index.faiss"
CHUNKS_PATH=BASE_DIR/"rag_faiss"/"chunks.json"
