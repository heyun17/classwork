from dotenv import load_dotenv

load_dotenv(override=True)

from langsmith import Client, traceable
from langchain_openai import ChatOpenAI

client = Client()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


@traceable(name="GPT 질문 테스트", client=client)
def ask(question: str) -> str:
    response = llm.invoke(question)
    return str(response.content)


result = ask("파이썬에서 리스트가 뭐야?")
print(result)

client.flush()