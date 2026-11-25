from clients import get_opensearch_client
from config import FAISS_INDEX_PATH, CHUNKS_PATH, SALES_INDEX

os_client = get_opensearch_client()

print("FAISS index:", FAISS_INDEX_PATH.exists())
print("chunks.json:", CHUNKS_PATH.exists())
print("sales index:", os_client.indices.exists(index=SALES_INDEX))
if os_client.indices.exists(index=SALES_INDEX):
    print("sales count:", os_client.count(index=SALES_INDEX)["count"])
