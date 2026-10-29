from toy_core import encode, lookup, add_position
for s in ['파이썬 좋아','함수 좋아 파이썬']:
    _,ids,mask=encode(s)
    print(s, '\n기본:',lookup(ids),'\n위치 추가:',add_position(ids))
