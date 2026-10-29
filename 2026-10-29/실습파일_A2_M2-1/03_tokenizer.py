"""교안 03: tokenize/encode/decode와 padding, truncation, token_type_ids.
모델은 글자를 직접 읽지 못하고 숫자(토큰 ID)만 받는다.
토크나이저가 문장을 어떻게 쪼개고 숫자로 바꾸는지, 여러 문장을 한 번에 넣을 때
길이를 어떻게 맞추는지 확인한다. 토크나이저 파일만 내려받으므로 가볍게 실행된다.
"""
from transformers import AutoTokenizer

# klue/bert-base: 한국어 BERT 모델 (WordPiece 방식 토크나이저 사용)
name = "klue/bert-base"
tok = AutoTokenizer.from_pretrained(name)

sentence = "이미지에 대체 텍스트를 제공해야 합니다."
print("원문:", sentence)

# tokenize: 문장 → 토큰(문자열) 목록
# - WordPiece는 자주 쓰이는 단어 조각 단위로 쪼갠다
# - '##'이 붙은 토큰은 앞 토큰에 이어지는 조각이라는 뜻 (예: '이미지' + '##에' = '이미지에')
print("토큰:", tok.tokenize(sentence))

# encode: 문장 → 토큰 ID(숫자) 목록. 모델에 실제로 들어가는 값이다
# - 기본적으로 앞뒤에 특수 토큰 [CLS](시작), [SEP](끝)의 ID가 자동으로 붙는다
#   그래서 위 토큰 개수보다 ID가 2개 더 많다
ids = tok.encode(sentence)
print("ID:", ids)

# convert_ids_to_tokens: ID → 토큰 문자열. 특수 토큰이 붙은 것을 눈으로 확인할 수 있다
print("ID→토큰:", tok.convert_ids_to_tokens(ids))

# decode: ID → 원래 문장으로 복원
# - skip_special_tokens=True: [CLS], [SEP] 같은 특수 토큰은 빼고 복원
print("디코딩:", tok.decode(ids, skip_special_tokens=True))

# special_tokens_map: 이 토크나이저가 쓰는 특수 토큰 목록
# - [UNK]: 사전에 없는 토큰, [PAD]: 길이 맞추기용 빈칸, [MASK]: 가려진 토큰(사전학습용)
print("특수토큰:", tok.special_tokens_map)

# 여러 문장을 한 번에(batch) 토큰화
# - 문장마다 길이가 다르면 텐서(행렬)로 묶을 수 없으므로 길이를 맞춰야 한다
# - padding=True: 가장 긴 문장 길이에 맞춰 짧은 문장 뒤에 [PAD](ID 0)를 채운다
# - truncation=True + max_length=32: 32토큰보다 길면 뒤를 잘라낸다
# - return_tensors="pt": 결과를 PyTorch 텐서로 돌려준다
inputs = tok([sentence, "WCAG 2.4.4 링크 목적 확인"], padding=True,
             truncation=True, max_length=32, return_tensors="pt")

# 결과는 세 가지 텐서로 구성되며, shape은 [문장 수, 맞춰진 길이]
# - input_ids: 토큰 ID. 짧은 첫 문장 끝에 0([PAD])이 채워진 것을 볼 수 있다
# - token_type_ids: 문장 구분 번호. 문장 2개를 한 입력으로 넣을 때(질문+문단 등)
#   첫 문장은 0, 두 번째 문장은 1이 된다. 여기서는 각각 한 문장이라 모두 0
# - attention_mask: 실제 토큰은 1, [PAD]는 0. 모델이 패딩 부분을 무시하게 해 준다
print("\n[배치 토큰화 결과]")
for key, value in inputs.items():
    print(f"{key} {tuple(value.shape)}")
    for row in value.tolist():
        print("  ", row)

# 주의: truncation은 max_length를 넘는 부분을 그냥 버린다
# RAG에서 긴 문서를 그대로 넣으면 뒤쪽에 있던 근거가 잘려 사라질 수 있으므로
# 문서를 미리 적당한 길이로 나눠(chunking) 넣는 것이 좋다
print("\ntruncation=True는 길이를 넘는 부분을 잘라내므로 근거 손실을 유발할 수 있습니다.")
