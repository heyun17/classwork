# Dockerfile
FROM python:3.12-slim
WORKDIR /app

# 라이브러리 목록을 먼저 복사해 설치한다 (코드보다 덜 바뀌므로 위에 둔다)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 그다음 코드를 복사한다
COPY report.py .

# 컨테이너가 시작되면 실행할 명령
CMD ["python", "report.py"]
