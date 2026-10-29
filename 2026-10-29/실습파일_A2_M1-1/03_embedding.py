from toy_core import encode, lookup, masked_mean
_, ids, mask = encode('파이썬 좋아')
vectors=lookup(ids)
print('토큰 ID:',ids)
print('토큰 임베딩:',vectors)
print('패딩 포함 평균:',[sum(v[j] for v in vectors)/len(vectors) for j in range(2)])
print('패딩 제외 평균:',masked_mean(vectors,mask))
