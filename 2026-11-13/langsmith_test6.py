from dotenv import load_dotenv

load_dotenv(override=True)

import re
import pandas as pd

from langsmith import Client, traceable
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


# ============================================================
# 1. LangSmith 클라이언트
# ============================================================

client = Client()


# ============================================================
# 2. CSV 불러오기
# ============================================================

df = pd.read_csv("감기환자 진료 데이터.csv")


# ============================================================
# 3. CSV → Document 변환
# ============================================================

documents = [
    Document(
        page_content=row["진료내용"],
        metadata={
            "환자ID": row["환자ID"]
        }
    )
    for _, row in df.iterrows()
]


# ============================================================
# 4. FAISS 벡터 DB
# ============================================================

db = FAISS.from_documents(
    documents,
    OpenAIEmbeddings()
)


# ============================================================
# 5. 답변 생성용 LLM
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ============================================================
# 6. 검색
#
# v3:
# - 환자ID가 질문에 있으면 정확 일치 검색
# - 그 외 질문은 기존 FAISS 의미 검색
# ============================================================

@traceable(name="검색", client=client)
def retrieve(question: str) -> dict:

    # --------------------------------------------------------
    # 6-1. 환자ID 정확 일치 검색
    # --------------------------------------------------------

    match = re.search(r"\bP\d{3}\b", question)

    if match:
        patient_id = match.group()

        matched_docs = [
            doc
            for doc in documents
            if doc.metadata["환자ID"] == patient_id
        ]

        if not matched_docs:
            return {
                "found": False,
                "context": ""
            }

        context = "\n\n".join(
            f"[{doc.metadata['환자ID']}] {doc.page_content}"
            for doc in matched_docs
        )

        return {
            "found": True,
            "context": context
        }


    # --------------------------------------------------------
    # 6-2. 일반 질문 → FAISS 의미 검색
    # --------------------------------------------------------

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


# ============================================================
# 7. 답변 생성
#
# 특정 정답 표현을 유도하지 않음.
# 검색된 자료에서 질문과 관련된 사실을 빠짐없이 답하게만 함.
# ============================================================

@traceable(name="답변생성", client=client)
def generate_answer(question: str, context: str) -> str:

    prompt = f"""
아래 진료기록만 근거로 질문에 답하세요.

답변 규칙:
1. 질문에 직접적으로 답하세요.
2. 검색된 진료기록 중 질문과 관련된 사실을 빠뜨리지 마세요.
3. 여러 환자나 여러 사례에 관한 질문이면 관련 기록을 종합해서 답하세요.
4. 필요한 경우 환자ID를 함께 제시하세요.
5. 진료기록에 없는 내용은 추측하지 마세요.

진료기록:
{context}

질문:
{question}
"""

    response = llm.invoke(prompt)

    return str(response.content)


# ============================================================
# 8. 전체 RAG
# ============================================================

@traceable(name="진료RAG", client=client)
def rag(question: str) -> str:

    result = retrieve(question)

    if not result["found"]:
        return "관련 진료기록을 찾지 못했습니다."

    return generate_answer(
        question,
        result["context"]
    )


# ============================================================
# 9. 평가용 LLM
# ============================================================

judge_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ============================================================
# 10. 평가자 1 - 의미일치
#
# 특정 정답을 하드코딩하지 않고,
# reference와 actual의 의미만 비교
# ============================================================

def 의미일치(
    outputs: dict,
    reference_outputs: dict
) -> bool:

    actual = outputs["answer"]
    reference = reference_outputs["answer"]

    prompt = f"""
모범답안과 실제 답변의 의미를 비교하세요.

판정 기준:
- 핵심 사실이 서로 같으면 YES
- 표현이나 문장 구조가 달라도 의미가 같으면 YES
- 실제 답변에 올바른 추가 설명이 있어도 핵심 의미가 같으면 YES
- 핵심 사실이 다르거나 서로 모순되면 NO
- 같은 사실을 서로 다른 자연어 표현으로 말한 경우에는 YES

모범답안:
{reference}

실제 답변:
{actual}

YES 또는 NO만 출력하세요.
"""

    response = judge_llm.invoke(prompt)

    result = str(response.content).strip().upper()

    return result == "YES"


# ============================================================
# 11. 평가자 2 - 정답포함
#
# 특정 약 이름이나 현재 평가 문제의 정답을 하드코딩하지 않음.
# 모범답안의 핵심 사실이 실제 답변에 모두 들어있는지만 평가.
# ============================================================

def 정답포함(
    inputs: dict,
    outputs: dict,
    reference_outputs: dict
) -> bool:

    question = inputs["question"]
    actual = outputs["answer"]
    reference = reference_outputs["answer"]

    prompt = f"""
원래 질문과 모범답안을 기준으로,
모범답안의 핵심 정답 정보가 실제 답변에 모두 포함되어 있는지 판단하세요.

판정 기준:
- 원래 질문의 의도를 기준으로 판단하세요.
- 모범답안의 핵심 사실이 실제 답변에 모두 포함되어 있으면 YES입니다.
- 표현이나 문장 구조가 달라도 의미가 같으면 YES입니다.
- 실제 답변에 추가적인 올바른 설명이 있어도 감점하지 않습니다.
- 모범답안의 핵심 사실이 빠졌거나 실제 답변과 모순되면 NO입니다.

원래 질문:
{question}

모범답안:
{reference}

실제 답변:
{actual}

YES 또는 NO만 출력하세요.
"""

    response = judge_llm.invoke(prompt)

    return str(response.content).strip().upper() == "YES"


# ============================================================
# 12. LangSmith 평가용 target
# ============================================================

def target(inputs: dict) -> dict:

    question = inputs["question"]

    answer = rag(question)

    return {
        "answer": answer
    }


# ============================================================
# 13. 기존 평가 데이터셋
# ============================================================

dataset_name = "진료RAG-평가셋"


# ============================================================
# 14. v3 평가
# ============================================================

results = client.evaluate(
    target,
    data=dataset_name,
    evaluators=[
        의미일치,
        정답포함
    ],
    experiment_prefix="진료RAG-v4",

    # 평가를 순차적으로 진행
    max_concurrency=1
)


print("평가 완료:", results.experiment_name)