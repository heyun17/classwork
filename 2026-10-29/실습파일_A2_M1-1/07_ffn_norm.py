import math
x=[1.,-2.]
relu=[max(0.,v) for v in x]
print('FFN 중간 활성화(ReLU):',relu)
y=[1.,2.]; f=[0.2,-0.5]
print('Residual:',[a+b for a,b in zip(y,f)])
z=[1.,3.]; mu=sum(z)/len(z)
variance=sum((v-mu)**2 for v in z)/len(z)
print('LayerNorm 기본 표준화:',[(v-mu)/math.sqrt(variance+1e-5) for v in z])
