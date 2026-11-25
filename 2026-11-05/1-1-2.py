import json
import unicodedata


def find_special_characters_in_jsonl(file_path):
    """JSONL 파일에서 특수문자를 찾아 행 번호와 함께 출력합니다."""

    # 일반적인 문자(L), 숫자(N), 공백(Zs)을 제외한 카테고리를 특수문자로 정의
    # P: 문장부호, S: 기호, C: 기타(제어문자, 이모지 등)
    target_categories = ("P", "S", "C")

    print(f"🔍 {file_path} 파일에서 특수문자 탐색을 시작합니다...\n")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                try:
                    # JSON 데이터 파싱 (문자열 전체를 검사하려면 line 자체를 써도 됩니다)
                    data = json.loads(line.strip())

                    # JSON 데이터를 문자열로 다시 변환하여 검사 (모든 키와 값 포함)
                    content_str = json.dumps(
                        data, ensure_ascii=False
                    )

                    special_chars_found = []

                    for char in content_str:
                        # 유니코드 카테고리 가져오기 (예: 'Ll', 'Zs', 'Pd', 'Sm' 등)
                        category = unicodedata.category(char)

                        # 시작 글자가 P, S, C로 시작하는지 확인 (단, JSON 구조용 기본 기호인 { } [ ] " , : 은 제외 가능)
                        # 여기서는 순수 데이터 내의 특수문자 탐색을 위해 기본 JSON 기호도 포함해서 찾습니다.
                        if category.startswith(target_categories):
                            # 필요에 따라 일반적인 문장부호(. , ! ?)나 JSON 기호를 제외하고 싶다면 아래 조건문을 추가하세요.
                            if char in '}{[]":,':
                                continue

                            # 유니코드 이름 가져오기
                            try:
                                char_name = unicodedata.name(char)
                            except ValueError:
                                char_name = "UNKNOWN NAME"

                            special_chars_found.append(
                                f"'{char}' ({category}: {char_name})"
                            )

                    # 중복 제거 및 결과 출력
                    if special_chars_found:
                        unique_chars = sorted(list(set(special_chars_found)))
                        print(f"📄 [Line {line_idx}]에서 특수문자 발견!")
                        print(f"   ↳ 발견된 문자: {', '.join(unique_chars)}")
                        print("-" * 50)

                except json.JSONDecodeError:
                    print(
                        f"⚠️ [Line {line_idx}] JSON 파싱 실패 (올바른 JSON 형식이 아닙니다.)"
                    )

    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")


# 💡 사용 예시
# 검사하고 싶은 jsonl 파일 경로를 넣어주세요.
file_path = "D:/OneDrive/#classes/November/1105/classwork/data/travel_raw.jsonl"
find_special_characters_in_jsonl(file_path)
