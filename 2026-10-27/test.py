from kiwipiepy import Kiwi
kiwi = Kiwi()

text = "배달이 너무 늦고 음식이 정말 맛있어요."
for t in kiwi.tokenize(text):
    if t.tag in ("VV", "VA", "MAG"):
        print(t.form, t.tag)

kiwi.add_user_word("배달앱", "NNG")
for t in kiwi.tokenize("배달앱에서 결제가 안 돼요"):
    print(t.form, t.tag)