from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
parser = StrOutputParser()

docs = pd.read_csv("travel_docs.csv")      # doc_id, category, source, title, body
print(docs.shape)

# 문서 번호 하나로 자료 가져오기
def get_doc(doc_id: str) -> str:
    r = docs[docs["doc_id"] == doc_id].iloc[0]
    return f"[{r['doc_id']}] {r['title']}\n{r['body']}"

# 문서 번호 여러 개를 한 번에
def get_docs(doc_ids: list) -> str:
    return "\n\n".join(get_doc(i) for i in doc_ids)

print(get_doc("T02"))