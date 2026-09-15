import requests

url = "https://pokeapi.co/api/v2/pokemon/pikachu"
res = requests.get(url, timeout=10)

print(res.status_code)              # 200
print(len(res.content), "바이트")     # 응답 크기

data = res.json()                   # JSON → 파이썬 딕셔너리
print(data["name"], data["id"])