import json
import hashlib

input_file = r"D:\OneDrive\#classes\November\1105\classwork\data\travel_normalized.jsonl"
output_file = r"D:\OneDrive\#classes\November\1105\classwork\data\travel_dedup.jsonl"


seen = set()
kept = []
removed = []


with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)

        # 정제 + 정규화가 끝난 text를 기준으로 해시값 생성
        text_hash = hashlib.md5(
            data["text"].encode("utf-8")
        ).hexdigest()

        # 이미 같은 내용이 있었다면 중복으로 제거
        if text_hash in seen:
            removed.append(data["raw_id"])
            continue

        # 처음 나온 문서는 유지
        seen.add(text_hash)
        kept.append(data)


# 중복 제거 결과 저장
with open(output_file, "w", encoding="utf-8") as out:
    for data in kept:
        out.write(
            json.dumps(data, ensure_ascii=False) + "\n"
        )


# ==================================================
# 중복 제거 검증
# ==================================================

print("===== 중복 제거 결과 =====")
print("제거 전 문서 수:", len(kept) + len(removed))
print("제거 후 문서 수:", len(kept))
print("제거된 문서 수:", len(removed))
print("제거된 raw_id:", removed)

print(f"\n중복 제거 완료: {output_file}")