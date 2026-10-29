"""교안 05: Pipeline Task와 BART. 큰 모델은 옵션으로 단계별 사용.
pipeline에 Task 이름만 바꿔 주면 분류·빈칸 채우기·요약·제로샷 분류를 같은 방식으로 실행할 수 있다.
모델이 클수록 다운로드와 실행이 오래 걸리므로 --task 옵션으로 하나씩 골라 실행한다.

실행 예:
  python 05_pipeline_bart.py                    # 기본: classify (한국어 감성 분류)
  python 05_pipeline_bart.py --task mask        # 빈칸 채우기 (bart-base, 약 0.5GB)
  python 05_pipeline_bart.py --task summary     # 요약 (bart-large-cnn, 약 1.6GB)
  python 05_pipeline_bart.py --task zero-shot   # 제로샷 분류 (bart-large-mnli, 약 1.6GB)
"""
import argparse
from transformers import AutoTokenizer, pipeline

# argparse: 명령줄 옵션(--task)을 받아 실행할 Task를 고른다
parser = argparse.ArgumentParser()
parser.add_argument("--task", choices=["classify", "mask", "summary", "zero-shot"], default="classify")
args = parser.parse_args()

if args.task == "classify":
    # text-classification: 문장 → 정해진 라벨 중 하나로 분류 (02에서 사용한 모델과 동일)
    # - model, tokenizer에 모델 ID 문자열을 주면 pipeline이 알아서 불러온다
    # - device=-1: CPU 사용
    model = "snunlp/KR-FinBert-SC"
    task = pipeline("text-classification", model=model, tokenizer=model, device=-1)
    # top_k=None: 모든 라벨 점수를 높은 순으로 출력
    print(task("기업 실적이 개선되었다.", top_k=None))

elif args.task == "mask":
    # fill-mask: 문장 속 가려진 자리(마스크 토큰)에 들어갈 단어를 예측
    # - BART는 사전학습 때 가려진 부분을 복원하도록 학습되어 빈칸 채우기를 할 수 있다
    # - 영어 모델이므로 영어 문장을 넣어야 한다
    name = "facebook/bart-base"
    tok = AutoTokenizer.from_pretrained(name)
    task = pipeline("fill-mask", model=name, tokenizer=tok, device=-1)
    # 마스크 토큰은 모델마다 다르다 (BERT는 [MASK], BART는 <mask>)
    # 그래서 문자열을 직접 쓰지 않고 tok.mask_token으로 가져온다
    # top_k=3: 점수가 높은 후보 3개만 출력
    print(task(f"I went to the {tok.mask_token} today.", top_k=3))

elif args.task == "summary":
    # 요약: 긴 글 → 짧은 요약문 생성
    # - bart-large-cnn: CNN/DailyMail 뉴스 요약 데이터로 파인튜닝된 영어 요약 모델
    # - transformers v5부터 "summarization" pipeline이 삭제되어,
    #   pipeline 대신 모델을 직접 불러와 generate()로 요약문을 생성한다
    # - AutoModelForSeq2SeqLM: 입력 문장을 읽고(인코더) 새 문장을 써 내는(디코더) 모델
    from transformers import AutoModelForSeq2SeqLM
    name = "facebook/bart-large-cnn"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSeq2SeqLM.from_pretrained(name)
    # 같은 문장을 15번 반복해 긴 입력을 만든다
    text = ("Artificial intelligence can analyze long reports and organize information. " * 15)
    # 토큰화 (BART 최대 입력 1024토큰을 넘으면 잘라냄)
    inputs = tok(text, truncation=True, max_length=1024, return_tensors="pt")
    # generate: 요약문 토큰을 한 개씩 생성
    # - max_new_tokens=50: 요약문을 최대 50토큰까지만 생성
    # - min_length=10: 모델 기본 설정의 최소 길이(56)가 최대 길이보다 커서 경고가 나므로 낮춰 준다
    # - do_sample=False: 무작위 샘플링 없이 가장 확률 높은 단어를 골라 매번 같은 결과가 나온다
    summary_ids = model.generate(**inputs, max_new_tokens=50, min_length=10, do_sample=False)
    # decode: 생성된 토큰 ID → 문장 (특수 토큰 제외)
    print([{"summary_text": tok.decode(summary_ids[0], skip_special_tokens=True)}])

else:
    # zero-shot-classification: 따로 학습하지 않은 라벨로도 분류
    # - bart-large-mnli: 두 문장이 서로 맞는지(함의/모순) 판단하도록 학습된 모델
    # - 원리: 라벨마다 "This text is about {라벨}." 문장을 만들고
    #   입력 문장과 얼마나 잘 맞는지(함의 확률)를 점수로 사용한다
    # - 그래서 후보 라벨(technology, sports)을 실행할 때 마음대로 바꿀 수 있다
    task = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)
    result = task("A new smartphone has an improved camera.", ["technology", "sports"],
                  hypothesis_template="This text is about {}.")
    # 결과: sequence(입력 문장), labels(점수 높은 순 라벨), scores(라벨별 점수, 합계 1)
    print(result)

# Task마다 모델 크기, 지원 언어(한국어/영어), 라벨 정의가 다르므로
# 실제로 쓰기 전에 Hub의 모델 카드에서 꼭 확인해야 한다
print("Task별 모델 크기와 입력 언어·라벨 정의를 확인하세요.")
