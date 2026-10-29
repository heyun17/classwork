from toy_core import SENTENCES, VOCAB, encode
print('어휘 사전:', VOCAB)
for s in SENTENCES:
    print(s, '=>', encode(s))
print('OOV:', encode('비행기 좋아'))
