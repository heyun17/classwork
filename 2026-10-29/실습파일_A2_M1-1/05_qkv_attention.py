from toy_core import qkv_from_x, scaled_dot_attention
x=[[1.,0.],[0.,1.]]
qkv=[qkv_from_x(v) for v in x]
print('QKV:',qkv)
query=qkv[1][0]
keys=[r[1] for r in qkv]
values=[r[2] for r in qkv]
s,w,c=scaled_dot_attention(query,keys,values)
print('스케일 점수:',s)
print('Softmax 가중치:',w)
print('V 가중합:',c)
