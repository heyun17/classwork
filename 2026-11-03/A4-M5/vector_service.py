import json,faiss
from config import *
def load_existing_faiss():
    index=faiss.read_index(str(FAISS_INDEX_PATH))
    chunks=json.load(open(CHUNKS_PATH,encoding="utf-8"))
    return index,chunks
def create_vector_index(c,dimension,recreate=False):
    if c.indices.exists(index=RAG_INDEX):
        if recreate:c.indices.delete(index=RAG_INDEX)
        else:return False
    c.indices.create(index=RAG_INDEX,body={"settings":{"index":{"knn":True}},"mappings":{"properties":{"chunk_id":{"type":"integer"},"title":{"type":"keyword"},"content":{"type":"text"},"embedding":{"type":"knn_vector","dimension":dimension,"method":{"name":"hnsw","space_type":"cosinesimil","engine":"faiss"}}}}})
    return True
def transfer_faiss_vectors(c,index,chunks):
    for i,chunk in enumerate(chunks):
        c.index(index=RAG_INDEX,id=i,body={"chunk_id":i,"title":chunk.splitlines()[0].replace("## ",""),"content":chunk,"embedding":index.reconstruct(i).tolist()})
    c.indices.refresh(index=RAG_INDEX)
def knn_search(ai,c,q,k=3):
    v=ai.embeddings.create(model=EMBEDDING_MODEL,input=q).data[0].embedding
    return c.search(index=RAG_INDEX,body={"size":k,"_source":["chunk_id","title","content"],"query":{"knn":{"embedding":{"vector":v,"k":k}}}})["hits"]["hits"]
