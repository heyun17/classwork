from toy_core import SENTENCES, encode
for s in SENTENCES:
    words, ids, mask = encode(s)
    print(s, '\n  원본 길이:',len(words),'ID:',ids,'Mask:',mask)
try:
    encode('하나 둘 셋 넷 다섯')
except ValueError as e:
    print('길이 초과 예상 오류:',e)
