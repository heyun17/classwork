# ====================================================================
# 파일 용도: 참고용: CSV 100건을 Python에서 OpenSearch sales 인덱스로 업로드합니다. Part 0과 중복되어 필수 실습에서는 제외합니다.
# ====================================================================

from clients import get_opensearch_client
from sales_service import (
    read_sales_csv,
    create_sales_index_if_needed,
    upload_sales_dataframe,
)

os_client = get_opensearch_client()

df = read_sales_csv()

created = create_sales_index_if_needed(
    os_client
)

if created:
    print("sales 인덱스를 새로 생성했습니다.")
else:
    print("기존 sales 인덱스를 사용합니다.")

success, errors = upload_sales_dataframe(
    os_client,
    df
)

print("업로드 성공:", success)
print("오류 건수:", len(errors))
print(
    "현재 sales 문서 수:",
    os_client.count(index="sales")["count"]
)
