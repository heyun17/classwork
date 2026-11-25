from dotenv import load_dotenv
load_dotenv(override=True)

import pandas as pd

from langsmith import Client, traceable
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


client = Client()

# 1. 진료 데이터 → Document
df = pd.read_csv("감기환자 진료 데이터.csv")

documents = [
    Document(
        page_content=row["진료내용"],
        metadata={"환자ID": row["환자ID"]}
    )
    for _, row in df.iterrows()
]

# 2. 실제 FAISS 벡터DB 생성
db = FAISS.from_documents(
    documents,
    OpenAIEmbeddings()
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# 3. 검색
@traceable(name="검색", client=client)
def retrieve(question: str) -> dict:
    results = db.similarity_search_with_relevance_scores(
        question,
        k=2
    )

    filtered = [
        (doc, score)
        for doc, score in results
        if score >= 0.75
    ]

    if not filtered:
        return {
            "found": False,
            "context": ""
        }

    context = "\n\n".join(
        f"[{doc.metadata['환자ID']}] {doc.page_content}"
        for doc, score in filtered
    )

    return {
        "found": True,
        "context": context
    }


# 4. 답변 생성
@traceable(name="답변생성", client=client)
def generate_answer(question: str, context: str) -> str:
    prompt = f"""
아래 진료기록만 참고하여 질문에 답하세요.

진료기록:
{context}

질문:
{question}
"""

    response = llm.invoke(prompt)
    return str(response.content)


# 5. 전체 RAG
@traceable(name="진료RAG", client=client)
def rag(question: str) -> str:
    result = retrieve(question)

    if not result["found"]:
        return "관련 진료기록을 찾지 못했습니다."

    return generate_answer(
        question,
        result["context"]
    )


#answer = rag("급성 기관지염 환자들은 어떤 처방을 받았어?")
#print(answer)

#client.flush()

#answer = rag("우주여행 비용은 얼마야?")
#print(answer)

#client.flush()


dataset_name = "진료RAG-평가셋"

dataset = client.create_dataset(
    dataset_name=dataset_name,
    description="진료 RAG 평가용 질문과 모범답안"
)

examples = [
    {
        "inputs": {
            "question": "급성 기관지염 환자들은 어떤 처방을 받았어?"
        },
        "reference_outputs": {
            "answer": "종합감기약과 진해거담제를 처방받았습니다."
        },
    },
    {
        "inputs": {
            "question": "P024 환자의 진단명은 뭐야?"
        },
        "reference_outputs": {
            "answer": "급성 기관지염"
        },
    },
    {
        "inputs": {
            "question": "우주여행 비용은 얼마야?"
        },
        "reference_outputs": {
            "answer": "관련 진료기록 없음"
        },
    },
    {
        "inputs": {
            "question": "P002 환자는 어떤 처방을 받았어?"
        },
        "reference_outputs": {
            "answer": "진해거담제"
        },
    },
]

client.create_examples(
    dataset_name=dataset_name,
    examples=examples
)

print("평가 데이터셋 생성 완료")