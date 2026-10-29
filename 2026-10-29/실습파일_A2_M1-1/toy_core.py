"""A2-M1 교육용: 고정 어휘, 패딩, 임베딩, 위치, QKV 계산 (표준 라이브러리만 사용)."""
import math

SENTENCES = ['파이썬 좋아', '하늘 파랗고 좋아', '함수 좋아 파이썬']
VOCAB = {'[PAD]': 0, '[UNK]': 1, '파이썬': 2, '좋아': 3,
         '하늘': 4, '파랗고': 5, '함수': 6}
MAX_LEN = 4
EMBEDDINGS = [
    [0.0, 0.0], [0.1, 0.1], [1.0, 0.0], [0.0, 1.0],
    [1.0, 1.0], [1.0, 0.5], [0.8, 0.2],
]
POSITION_VECTORS = [[0.1, 0.0], [0.0, 0.1], [0.2, 0.0], [0.0, 0.2]]
WQ = [[0.0, 1.0], [1.0, 0.0]]
WK = [[1.0, 0.0], [0.0, 1.0]]
WV = [[2.0, 0.0], [0.0, 4.0]]


def encode(sentence):
    """(공백 토큰 목록, 길이 4 ID, 길이 4 마스크)를 반환. 길이 초과 시 예외."""
    words = sentence.split()
    if len(words) > MAX_LEN:
        raise ValueError(f'토큰 수 {len(words)}: 최대 {MAX_LEN}개까지 허용')
    ids = []
    for word in words:
        ids.append(VOCAB.get(word, VOCAB['[UNK]']))
    mask = [1] * len(ids)
    while len(ids) < MAX_LEN:
        ids.append(VOCAB['[PAD]'])
        mask.append(0)
    return words, ids, mask


def lookup(ids):
    return [EMBEDDINGS[token_id][:] for token_id in ids]


def masked_mean(vectors, mask):
    count = sum(mask)
    if count == 0:
        raise ValueError('유효 토큰이 없어 평균을 계산할 수 없습니다.')
    width = len(vectors[0])
    sums = [0.0] * width
    for vector, valid in zip(vectors, mask):
        if valid:
            for j in range(width):
                sums[j] += vector[j]
    return [value / count for value in sums]


def add_position(ids):
    results = []
    for i, token_id in enumerate(ids):
        vec = EMBEDDINGS[token_id][:]
        if token_id != VOCAB['[PAD]']:
            vec = [vec[j] + POSITION_VECTORS[i][j] for j in range(2)]
        results.append(vec)
    return results


def matvec(x, matrix):
    # 행벡터 x와 행렬 matrix의 곱: y[j] = sum(x[i]*matrix[i][j])
    return [sum(x[i] * matrix[i][j] for i in range(len(x))) for j in range(len(matrix[0]))]


def qkv_from_x(x):
    return matvec(x, WQ), matvec(x, WK), matvec(x, WV)


def softmax(scores):
    if not scores:
        raise ValueError('점수가 비어 있습니다.')
    m = max(scores)
    exp_values = [math.exp(s - m) for s in scores]
    total = sum(exp_values)
    return [x / total for x in exp_values]


def scaled_dot_attention(query, keys, values):
    if not keys or len(keys) != len(values):
        raise ValueError('Key와 Value가 없거나 길이가 다릅니다.')
    d_k = len(query)
    scores = [sum(q * k for q, k in zip(query, key)) / math.sqrt(d_k) for key in keys]
    weights = softmax(scores)
    context = [sum(w * v[j] for w, v in zip(weights, values)) for j in range(len(values[0]))]
    return scores, weights, context


def causal_visibility(length):
    return [[1 if j <= i else 0 for j in range(length)] for i in range(length)]
