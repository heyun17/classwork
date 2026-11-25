import json
import re
import html

input_file = r"D:\OneDrive\#classes\November\1105\classwork\data\travel_raw.jsonl"
output_file = r"D:\OneDrive\#classes\November\1105\classwork\data\travel_clean.jsonl"

# 정제 검증용
html_tag_count = 0
nbsp_count = 0
star_count = 0
copyright_count = 0

with open(input_file, "r", encoding="utf-8") as f, \
     open(output_file, "w", encoding="utf-8") as out:

    for line in f:
        data = json.loads(line)
        page = data["html"]

        # 제목 추출 및 정제
        match = re.search(r"<h2>(.*?)</h2>", page, re.S)
        title = match.group(1) if match else ""
        title = re.sub(
            r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]",
            "",
            title
        ).strip()

        # 본문 정제
        t = re.sub(r"<h2>.*?</h2>", " ", page, flags=re.S)
        t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
        t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
        t = re.sub(r'<div class="footer">.*?</div>', " ", t, flags=re.S)
        t = re.sub(r"<[^>]+>", " ", t)
        t = html.unescape(t)
        t = re.sub(r"[★☆▶◀■□●○◆◇♥]", "", t)
        t = re.sub(
            r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]",
            "",
            t
        )
        t = re.sub(r"\s+", " ", t).strip()

        # 정제 전후 비교 샘플 2건
        if data["raw_id"] in ["R01", "R02"]:
            print(f"\n===== {data['raw_id']} 정제 전 =====")
            print(page)

            print(f"\n===== {data['raw_id']} 정제 후 =====")
            print(f"<{title}> {t}" if title else t)

        # 정제 후 노이즈 검사
        # '<' 자체가 아니라 실제 HTML 태그 형태만 검사
        html_tag_count += len(re.findall(r"</?[A-Za-z][^>]*>", t))
        nbsp_count += t.count("&nbsp;")
        star_count += t.count("★")
        copyright_count += t.count("Copyright")

        # 제목과 본문 결합
        clean_text = f"<{title}> {t}" if title else t

        # 원본 메타데이터 유지
        result = {
            "raw_id": data["raw_id"],
            "doc_id": data["doc_id"],
            "category": data["category"],
            "source": data["source"],
            "url": data["url"],
            "text": clean_text
        }

        # JSONL 저장
        out.write(json.dumps(result, ensure_ascii=False) + "\n")


print(f"\nJSONL 파일 저장 완료: {output_file}")

print("\n===== 정제 후 전체 노이즈 검사 =====")
print("HTML 태그:", html_tag_count, "건")
print("&nbsp;:", nbsp_count, "건")
print("★:", star_count, "건")
print("Copyright:", copyright_count, "건")

total_noise = (
    html_tag_count
    + nbsp_count
    + star_count
    + copyright_count
)

print("전체 노이즈:", total_noise, "건")