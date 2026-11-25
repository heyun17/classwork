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
# 4. FAISS 벡터 DB 생성
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
# - P024 같은 환자ID가 질문에 있으면 metadata 정확 검색
# - 환자ID가 없는 일반 질문은 FAISS 의미 검색
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
# 보는 정보:
# Question + Reference + Output
#
# 질문의 맥락까지 포함해서
# 전체 답변의 의미가 맞는지 평가
# ============================================================

def 의미일치(
    inputs: dict,
    outputs: dict,
    reference_outputs: dict
) -> bool:

    question = inputs["question"]
    actual = outputs["answer"]
    reference = reference_outputs["answer"]

    prompt = f"""
원래 질문을 기준으로
모범답안과 실제 답변의 핵심 의미가 같은지 판단하세요.

판정 기준:
- 질문의 의도를 기준으로 판단하세요.
- 모범답안과 실제 답변의 핵심 사실이 같으면 YES입니다.
- 표현이나 문장 구조가 달라도 의미가 같으면 YES입니다.
- 실제 답변에 추가적인 올바른 설명이 있어도 감점하지 않습니다.
- 핵심 사실이 다르거나 서로 모순되면 NO입니다.

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
# 11. 평가자 2 - 정답포함
#
# 보는 정보:
# Reference + Output
#
# 질문의 적절성을 평가하는 것이 아니라,
# 모범답안에 들어 있는 핵심 정답 정보가
# 실제 답변 안에 포함되어 있는지만 평가
# ============================================================

def 정답포함(
    outputs: dict,
    reference_outputs: dict
) -> bool:

    actual = outputs["answer"]
    reference = reference_outputs["answer"]

    prompt = f"""
모범답안에 포함된 핵심 정답 정보가
실제 답변에 모두 포함되어 있는지 판단하세요.

판정 기준:
- 모범답안의 핵심 사실이 실제 답변에 모두 포함되어 있으면 YES입니다.
- 표현이나 문장 구조가 다른 것은 허용합니다.
- 같은 의미를 다른 자연어 표현으로 작성한 것도 허용합니다.
- 실제 답변에 추가적인 올바른 설명이 있는 것은 허용합니다.
- 모범답안의 여러 핵심 사실이 하나의 문장에 함께 적혀 있어도,
  실제 답변에서 여러 문장이나 여러 대상에 나뉘어 나타날 수 있습니다.
  이 경우에도 핵심 사실이 모두 포함되어 있으면 YES입니다.
- 모범답안의 핵심 사실 중 하나라도 빠졌으면 NO입니다.
- 실제 답변이 모범답안과 모순되면 NO입니다.

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
# 14. v5 평가 실행
#
# test7.py이지만 LangSmith 실험 버전은
# v1 → v2 → v3 → v4 다음이므로 v5
# ============================================================

results = client.evaluate(
    target,
    data=dataset_name,
    evaluators=[
        의미일치,
        정답포함
    ],
    experiment_prefix="진료RAG-v5",
    max_concurrency=1
)


print("평가 완료:", results.experiment_name)