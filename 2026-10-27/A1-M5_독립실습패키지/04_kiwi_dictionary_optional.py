try:
    from kiwipiepy import Kiwi
except ImportError:
    raise SystemExit('먼저 python -m pip install kiwipiepy 를 실행하세요.')
text='메타정합검증 결과를 확인합니다.'
kiwi=Kiwi()
def show(label):
    print(label,[(t.form,t.tag) for t in kiwi.tokenize(text)])
show('등록 전:')
kiwi.add_user_word('메타정합검증','NNP',0.0)
show('등록 후:')
print('사용자 사전 적용이 검색 정확도 개선을 보장하지는 않습니다.')
