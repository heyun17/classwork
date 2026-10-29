# A1 rules.csv를 쓰지 않고 구조만 확인하는 교육용 예시입니다.
records=[
    {'rule_id':'R-DEMO-01','status':'applied','title':'이미지 alt 속성'},
    {'rule_id':'R-DEMO-02','status':'proposed','title':'바로가기 문구 제한'},
]
searchable=[]
for row in records:
    if row['status']=='applied':
        searchable.append({'text':row['title'],'metadata':{'rule_id':row['rule_id']}})
print('적용 상태 규칙 검색 후보:',searchable)
print('주의: 실제 A1 스키마·상태값은 원본 CSV에서 검증 후 사용')
