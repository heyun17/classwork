import csv, random

TYPES = ["풀", "불꽃", "물", "전기", "노말",
         "비행", "독", "땅", "에스퍼", "벌레"]

def make(path, n):
    """포켓몬 데이터 n마리를 CSV로 만든다."""
    random.seed(42)                      # 매번 같은 값이 나오게
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "type1", "type2", "generation",
                    "hp", "attack", "defense", "speed", "legendary"])

        for i in range(1, n + 1):
            t1 = random.choice(TYPES)
            # 30% 확률로 두 번째 타입을 가짐
            t2 = random.choice(TYPES) if random.random() < 0.3 else ""
            if t2 == t1:
                t2 = ""
            w.writerow([
                i,
                f"포켓몬{i:05d}",
                t1, t2,
                random.randint(1, 9),        # 세대
                random.randint(20, 255),     # hp
                random.randint(5, 190),      # 공격
                random.randint(5, 230),      # 방어
                random.randint(5, 180),      # 스피드
                1 if random.random() < 0.02 else 0,   # 2% 전설
            ])
    print(path, n, "행 생성")

make("data/pokemon_1k.csv", 1_000)
make("data/pokemon_100k.csv", 100_000)
make("data/pokemon_1m.csv", 1_000_000)