from dotenv import load_dotenv
load_dotenv(override=True)

import pandas as pd

from langsmith import Client, traceable
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


# =========================================================
# 1. 기본 설정
# =========================================================

client = Client()

df = pd.read_csv("감기환자 진료 데이터.csv")

documents = [
    Document(
        page_content=row["진료내용"],
        metadata={"환자ID": row["환자ID"]}
    )
    for _, row in df.iterrows()
]


# =========================================================
# 2. FAISS 벡터DB 생성
# =========================================================

db = FAISS.from_documents(
    documents,
    OpenAIEmbeddings()
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# =========================================================
# 3. 검색
# =========================================================

@traceable(name="검색", client=client)
def retrieve(question: str) -> dict:
    results = db.similarity_search_with_relevance_scores(
        question,
        k=2
    )

    # 관련도 0.75 이상만 사용
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


# =========================================================
# 4. 답변 생성
# =========================================================

@traceable(name="답변생성", client=client)
def generate_answer(question: str, context: str) -> str:
    prompt = f"""
아래 진료기록만 참고하여 질문에 답하세요.

답변할 때 관련 환자의 환자ID를 정확히 포함하세요.

진료기록:
{context}

질문:
{question}
"""

    response = llm.invoke(prompt)

    return str(response.content)


# =========================================================
# 5. 전체 RAG
# =========================================================

@traceable(name="진료RAG", client=client)
def rag(question: str) -> str:
    result = retrieve(question)

    if not result["found"]:
        return "관련 진료기록을 찾지 못했습니다."

    return generate_answer(
        question,
        result["context"]
    )


# =========================================================
# [5-2] 평가자 2개 만들기
# =========================================================

judge_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# 평가자 ① 의미일치
def 의미일치(outputs: dict, reference_outputs: dict) -> bool:
    actual = outputs["answer"]
    reference = reference_outputs["answer"]

    prompt = f"""
실제 답변과 모범답안의 의미가 같은지 판단하세요.

모범답안:
{reference}

실제 답변:
{actual}

의미가 같으면 YES,
다르면 NO만 출력하세요.
"""

    response = judge_llm.invoke(prompt)

    return str(response.content).strip().upper() == "YES"


# 평가자 ② 정답포함
def 정답포함(outputs: dict, reference_outputs: dict) -> bool:
    actual = outputs["answer"]
    reference = reference_outputs["answer"]

    # "A과 B"처럼 정답이 두 개면 둘 다 실제 답변에 있는지 확인
    if "과 " in reference:
        keywords = reference.split("과 ")

        return all(
            keyword.strip() in actual
            for keyword in keywords
        )

    return reference in actual


# 다음 평가 단계에서 사용할 데이터셋 이름
dataset_name = "진료RAG-평가셋"


# =========================================================
# [5-3] 평가 대상 함수
# =========================================================

def target(inputs: dict) -> dict:
    question = inputs["question"]

    answer = rag(question)

    return {
        "answer": answer
    }


# =========================================================
# [5-4] v1 평가 실행
# =========================================================

results = client.evaluate(
    target,
    data=dataset_name,
    evaluators=[
        의미일치,
        정답포함
    ],
    experiment_prefix="진료RAG-v2",
    max_concurrency=0
)

print("평가 완료:", results.experiment_name)