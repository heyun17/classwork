# ====================================================================
# A4-M0 · Windows PowerShell 명령 모음 (한 블록씩 복사해서 실행)
# 비밀번호는 아래 한 줄에서만 정하고, 나머지는 $env:OS_PW 를 씁니다.
# ====================================================================
$env:OS_PW = "여기에-강한-비밀번호"   # 대문자·소문자·숫자·특수문자 포함 8자 이상

# ---- [02탭] Docker 확인
docker version
docker compose version

# ---- [03탭] OpenSearch 실행 (보안 ON)
docker run -d --name opensearch `
  -p 9200:9200 `
  -e "discovery.type=single-node" `
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=$env:OS_PW" `
  -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" `
  -v opensearch-secure-data:/usr/share/opensearch/data `
  opensearchproject/opensearch:latest

# ---- [04탭] Dashboards 실행
docker run -d --name opensearch-dashboards `
  -p 5601:5601 `
  --add-host=host.docker.internal:host-gateway `
  -e 'OPENSEARCH_HOSTS=["https://host.docker.internal:9200"]' `
  opensearchproject/opensearch-dashboards:latest

# ---- [05탭] 확인
docker ps
curl.exe -k -u "admin:$env:OS_PW" https://localhost:9200

# ---- [07탭] Nori 설치 (실행 중인 컨테이너에)
docker exec opensearch /usr/share/opensearch/bin/opensearch-plugin list
docker exec opensearch /usr/share/opensearch/bin/opensearch-plugin install --batch analysis-nori
docker restart opensearch

# ---- [07탭] 설치 확인
docker exec opensearch /usr/share/opensearch/bin/opensearch-plugin list
docker exec opensearch /usr/share/opensearch/bin/opensearch-plugin list | findstr nori   # analysis-nori 한 줄이 나오면 OK
curl.exe -sk -u "admin:$env:OS_PW" "https://localhost:9200/_cat/plugins?v&s=component"   # 실행 중인 노드가 읽었는지

# (또는) 컨테이너 안으로 들어가서: docker exec -it opensearch bash → opensearch-plugin list → exit

# ---- [08탭] Nori를 이미지에 넣어 영구 설치 (선택)
docker build -t opensearch-nori:3.9.0 .
docker rm -f opensearch
docker run -d --name opensearch `
  -p 9200:9200 `
  -e "discovery.type=single-node" `
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=$env:OS_PW" `
  -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" `
  -v opensearch-secure-data:/usr/share/opensearch/data `
  opensearch-nori:3.9.0

# ---- [08탭] Nori 삭제 (먼저 Dev Tools에서 Nori를 쓰는 인덱스를 지우거나 옮길 것)
docker exec opensearch `
  /usr/share/opensearch/bin/opensearch-plugin remove analysis-nori
docker restart opensearch
docker exec opensearch `
  /usr/share/opensearch/bin/opensearch-plugin list      # analysis-nori 가 없어야 함
