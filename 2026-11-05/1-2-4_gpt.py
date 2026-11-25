import json
import re
import statistics

input_file = r"D:\OneDrive\#classes\November\1105\classwork\data\travel_dedup.jsonl"
output_file = r"D:\OneDrive\#classes\November\1105\classwork\data\chunks.jsonl"

# 1-1에서 정한 값 사용
CHUNK_SIZE = 80
OVERLAP = 40


def chunk_by_sentences(text, size, overlap):
    # 문장 단위로 분리
    sentences = [
        s for s in re.split(r"(?<=[.?!])\s+", text)
        if s
    ]

    chunks = []
    current = []

    for sentence in sentences:

        # 현재 청크에 새 문장을 넣었을 때 size를 넘는 경우
        if current and len(" ".join(current + [sentence])) > size:

            # 현재 청크 저장
            chunks.append(" ".join(current))

            # overlap만큼 이전 문장을 다음 청크에 남김
            keep = []
            length = 0

            for previous in reversed(current):
                if length + len(previous) > overlap:
                    break

                keep.insert(0, previous)
                length += len(previous)

            current = keep

        current.append(sentence)

    # 마지막 청크 저장
    if current:
        chunks.append(" ".join(current))

    return chunks


def split_title_and_body(text):
    """
    기존 형식:
    <제목> 본문

    제목과 본문을 분리
    """
    match = re.match(r"^<([^>]+)>\s*(.*)$", text, re.S)

    if match:
        title = match.group(1)
        body = match.group(2)
        return title, body

    return "", text


all_chunks = []


with open(input_file, "r", encoding="utf-8") as f:

    for line in f:
        data = json.loads(line)

        # 기존 <제목> 본문 분리
        title, body = split_title_and_body(data["text"])

        # 문장 기준 청킹
        pieces = chunk_by_sentences(
            body,
            CHUNK_SIZE,
            OVERLAP
        )

        # 청크별 정보 생성
        for i, piece in enumerate(pieces):

            chunk = {
                "chunk_id": f"{data['doc_id']}-{i}",
                "doc_id": data["doc_id"],
                "title": title,
                "category": data["category"],
                "text": f"[{title}] {piece}" if title else piece
            }

            all_chunks.append(chunk)


# chunks.jsonl 저장
with open(output_file, "w", encoding="utf-8") as out:
    for chunk in all_chunks:
        out.write(
            json.dumps(chunk, ensure_ascii=False) + "\n"
        )


# ==================================================
# 청킹 결과 검증
# ==================================================

lengths = [len(chunk["text"]) for chunk in all_chunks]

print("===== 청킹 결과 =====")
print("분할 방식: 문장 기준")
print("chunk size:", CHUNK_SIZE)
print("overlap:", OVERLAP)
print("전체 청크 수:", len(all_chunks))

print("\n===== 청크 길이 =====")
print("최소:", min(lengths))
print("최대:", max(lengths))
print("평균:", round(statistics.mean(lengths), 1))


# ==================================================
# 두 개 이상으로 분할된 문서 1건 출력
# ==================================================

doc_chunks = {}

for chunk in all_chunks:
    doc_id = chunk["doc_id"]

    if doc_id not in doc_chunks:
        doc_chunks[doc_id] = []

    doc_chunks[doc_id].append(chunk)


print("\n===== 두 개 이상으로 분할된 문서 =====")

for doc_id, chunks in doc_chunks.items():

    if len(chunks) >= 2:

        print("doc_id:", doc_id)

        for chunk in chunks:
            print(
                chunk["chunk_id"],
                ":",
                chunk["text"]
            )

        break


# ==================================================
# chunks.jsonl 앞 3줄 출력
# ==================================================

print("\n===== chunks.jsonl 앞 3줄 =====")

with open(output_file, "r", encoding="utf-8") as f:

    for i, line in enumerate(f):

        if i == 3:
            break

        print(line.rstrip())


print(f"\n저장 완료: {output_file}")

def remove_title(text):
    # [제목] 부분 제거
    return re.sub(r"^\[[^\]]+\]\s*", "", text)


def overlap_text(a, b):
    # 앞 청크 끝과 다음 청크 시작에서
    # 동일하게 겹치는 가장 긴 문자열 찾기
    for k in range(min(len(a), len(b)), 0, -1):
        if a[-k:] == b[:k]:
            return a[-k:]
    return ""


print("\n===== overlap 확인 =====")

found = False

for doc_id, chunks in doc_chunks.items():

    if len(chunks) < 2:
        continue

    for i in range(len(chunks) - 1):

        body1 = remove_title(chunks[i]["text"])
        body2 = remove_title(chunks[i + 1]["text"])

        overlap = overlap_text(body1, body2)

        if overlap:
            print("doc_id:", doc_id)
            print("앞 청크:", chunks[i]["chunk_id"])
            print("다음 청크:", chunks[i + 1]["chunk_id"])
            print("겹친 부분:", repr(overlap))
            print("겹친 길이:", len(overlap), "자")
            found = True
            break

    if found:
        break