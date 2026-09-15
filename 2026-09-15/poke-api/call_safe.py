import requests

def fetch(name):
    """포켓몬 하나를 가져온다. 실패하면 None."""
    url = f"https://pokeapi.co/api/v2/pokemon/{name}"
    try:
        res = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print("연결 실패:", e)          # 네트워크 자체가 안 될 때
        return None

    if res.status_code != 200:
        print(f"{name}: {res.status_code}")   # 404 등
        return None

    return res.json()

if __name__ == "__main__":
    for n in ("pikachu", "charizard", "없는포켓몬"):
        d = fetch(n)
        print(n, "성공" if d else "실패")
