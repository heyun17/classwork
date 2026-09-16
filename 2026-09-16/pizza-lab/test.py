import os
import threading
import webbrowser

from dotenv import load_dotenv
from flask import Flask, request, render_template_string
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

client = OpenAI()
model = os.getenv("OPENAI_MODEL")


HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>OpenAI 테스트</title>
</head>
<body>
    <h1>OpenAI 질문하기</h1>

    <form method="POST">
        <input
            type="text"
            name="question"
            placeholder="질문을 입력하세요"
            style="width: 400px;"
            required
        >
        <button type="submit">질문</button>
    </form>

    {% if answer %}
        <h2>답변</h2>
        <p>{{ answer }}</p>
    {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    answer = None

    if request.method == "POST":
        question = request.form["question"]

        response = client.responses.create(
            model=model,
            input=question
        )

        answer = response.output_text

    return render_template_string(
        HTML,
        answer=answer
    )


if __name__ == "__main__":
    threading.Timer(
        1,
        lambda: webbrowser.open("http://127.0.0.1:5000")
    ).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )