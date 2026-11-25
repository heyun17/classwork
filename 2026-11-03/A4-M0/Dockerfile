# ====================================================================
# Nori가 들어 있는 OpenSearch 이미지 만들기
#   docker exec로 설치한 플러그인은 컨테이너를 지우면 사라집니다.
#   이미지에 넣어 두면 몇 번을 새로 만들어도 Nori가 있습니다.
# 사용:  docker build -t opensearch-nori:3.9.0 .
# 버전:  지금 쓰는 OpenSearch 버전과 똑같이 맞춥니다 (curl ... :9200 의 version.number)
# ====================================================================
FROM opensearchproject/opensearch:3.9.0
RUN /usr/share/opensearch/bin/opensearch-plugin install --batch analysis-nori
