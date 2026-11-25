import json
import re
import unicodedata

input_file = r"D:\OneDrive\#classes\November\1105\classwork\data\travel_clean.jsonl"
output_file = r"D:\OneDrive\#classes\November\1105\classwork\data\travel_normalized.jsonl"


def normalize_text(text):
    # 1. 전각 문자 → 일반 문자
    text = unicodedata.normalize("NFKC", text)

    # 2. 제로폭 공백 제거
    text = text.replace("\u200b", "")

    # 3. 표기 불일치 통일
    text = re.sub(
        r"해온\s*호스피탈리티",
        "해온호스피탈리티",
        text
    )

    return text


with open(input_file, "r", encoding="utf-8") as f, \
     open(output_file, "w", encoding="utf-8") as out:

    for line in f:
        data = json.loads(line)

        # 정제된 text를 정규화
        data["text"] = normalize_text(data["text"])

        out.write(
            json.dumps(data, ensure_ascii=False) + "\n"
        )


print(f"정규화 완료: {output_file}")


# ==================================================
# 정규화 검증
# ==================================================

fullwidth_count = 0
zero_width_count = 0
wrong_name_count = 0
unified_name_count = 0

with open(output_file, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        text = data["text"]

        # 전각 ASCII 문자 검사
        fullwidth_count += len(
            re.findall(r"[\uFF01-\uFF5E]", text)
        )

        # 제로폭 공백 검사
        zero_width_count += text.count("\u200b")

        # 표기 통일 확인
        wrong_name_count += text.count("해온 호스피탈리티")
        unified_name_count += text.count("해온호스피탈리티")


print("\n===== 정규화 검증 =====")
print("전각 문자:", fullwidth_count, "건")
print("제로폭 공백:", zero_width_count, "건")
print("해온 호스피탈리티:", wrong_name_count, "건")
print("해온호스피탈리티:", unified_name_count, "건")