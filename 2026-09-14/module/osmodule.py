import os

# 현재 작업 폴더
print(os.getcwd())

# 폴더 안의 파일 목록 — dir / ls 에 해당
print(os.listdir("images"))

# 경로 합치기 — OS마다 다른 구분자를 알아서 처리
path = os.path.join("images", "sample.png")

# 파일 정보
print(os.path.exists(path))      # 있는지
print(os.path.getsize(path))     # 바이트 크기
print(os.path.basename(path))    # sample.png

# 폴더 만들기 — 이미 있어도 오류 나지 않게
os.makedirs("logs", exist_ok=True)