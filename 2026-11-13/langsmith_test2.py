from dotenv import load_dotenv

load_dotenv(override=True)

from langsmith import Client, traceable
from langchain_openai import ChatOpenAI

client = Client()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


@traceable(name="검색", client=client)
def search(question: str) -> dict:
    if "리스트" in question:
        return {
            "found": True,
            "context": "파이썬 리스트는 여러 값을 순서대로 저장하는 자료구조입니다."
        }

    return {
        "found": False,
        "context": ""
    }


@traceable(name="답변생성", client=client)
def generate_answer(question: str, context: str) -> str:
    prompt = f"""
다음 참고자료를 바탕으로 질문에 답하세요.

참고자료:
{context}

질문:
{question}
"""

    response = llm.invoke(prompt)
    return str(response.content)


@traceable(name="간단 RAG", client=client)
def rag(question: str) -> str:
    search_result = search(question)

    if not search_result["found"]:
        return "관련 자료를 찾지 못했습니다."

    return generate_answer(
        question,
        search_result["context"]
    )


result = rag("자바스크립트 배열이 뭐야?")
print(result)

client.flush()