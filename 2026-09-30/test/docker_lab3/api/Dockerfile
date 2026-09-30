# 매출 집계 API 이미지
FROM python:3.12-slim

WORKDIR /app

# 실행할 코드만 이미지에 넣는다 (데이터는 밖에서 붙인다)
COPY api.py .

# 이 컨테이너는 5000번으로 서비스한다는 표시
EXPOSE 5000

# 컨테이너가 시작되면 API 서버를 띄운다
CMD ["python", "api.py"]
