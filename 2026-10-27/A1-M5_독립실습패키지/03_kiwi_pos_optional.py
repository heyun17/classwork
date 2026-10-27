try:
    from kiwipiepy import Kiwi
except ImportError:
    raise SystemExit('먼저 python -m pip install kiwipiepy 를 실행하세요.')
kiwi=Kiwi()
for sentence in ['배송이 빠르지 않습니다','접근성이 좋지 않다','링크 이름을 확인하지 않았습니다']:
    print('\n원문:',sentence)
    tokens=kiwi.tokenize(sentence)
    for t in tokens:
        print(f'  {t.form:<12} {t.tag:<8} start={t.start} len={t.len}')
    print('명사만:',[t.form for t in tokens if t.tag.startswith('NN')])
    print('주의: 명사만 추출하면 부정/평가/어미 정보가 빠질 수 있음')
