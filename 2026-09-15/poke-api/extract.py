def extract(data):
    """API 응답에서 필요한 값만 꺼내 딕셔너리 하나로."""
    types = [t["type"]["name"] for t in data["types"]]
    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

    return {
        "id": data["id"],
        "name": data["name"],
        "type1": types[0],
        "type2": types[1] if len(types) > 1 else "",
        "height": data["height"],
        "weight": data["weight"],
        "hp": stats.get("hp", 0),
        "attack": stats.get("attack", 0),
        "defense": stats.get("defense", 0),
        "speed": stats.get("speed", 0),
        "image": data["sprites"]["front_default"],
    }

if __name__ == "__main__":
    from call_safe import fetch

    data = fetch("pikachu")
    if data:
        print(extract(data))
