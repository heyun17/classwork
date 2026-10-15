import os
import json
import base64

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


# =========================
# 1. 현재 파일 기준 경로
# =========================
BASE_DIR = Path(__file__).resolve().parent

IMAGE_PATH = BASE_DIR / "resnet18_feature_maps.png"
OUTPUT_PATH = BASE_DIR / "freeze_plan.json"


# =========================
# 2. .env 불러오기
# =========================
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY가 없습니다. test 폴더의 .env를 확인하세요."
    )

client = OpenAI(api_key=api_key)


# =========================
# 3. GPT가 선택할 수 있는 레이어
# =========================
LayerName = Literal[
    "conv1",
    "bn1",
    "layer1",
    "layer2",
    "layer3",
    "layer4"
]


# =========================
# 4. JSON 출력 구조
# =========================
class FreezePlan(BaseModel):
    freeze_layers: list[LayerName]
    train_layers: list[LayerName]

    boundary_layer: LayerName

    insight: str
    reason: str

    confidence: float


# =========================
# 5. 이미지 Base64 변환
# =========================
def encode_image(path):

    with open(path, "rb") as f:
        return base64.b64encode(
            f.read()
        ).decode("utf-8")


image_base64 = encode_image(IMAGE_PATH)


# =========================
# 6. GPT 분석 요청
# =========================
prompt = """
첨부 이미지는 ImageNet pretrained ResNet18에
MNIST 손글씨 샘플을 입력했을 때의
레이어별 feature map 시각화 결과다.

이미지 왼쪽의 레이어 이름과 각 행의 feature map을
순서대로 분석하라.

레이어 순서는 다음과 같다.

conv1
bn1
relu
maxpool
layer1
layer2
layer3
layer4

단, 실제 학습 파라미터 동결 여부를 결정할 대상은
다음 6개뿐이다.

conv1
bn1
layer1
layer2
layer3
layer4

relu와 maxpool은 학습 파라미터가 없으므로
freeze_layers와 train_layers에 넣지 마라.

목적은 ImageNet pretrained ResNet18을
MNIST 숫자 분류에 전이학습하는 것이다.

다음 내용을 시각적으로 분석하라.

- 초반 레이어에서 숫자의 윤곽과 edge가 얼마나 유지되는가
- layer1 이후 특징 표현이 어떻게 변하는가
- feature map이 지나치게 sparse해지는 시점
- 공간적 숫자 형태가 크게 손실되는 시점
- ImageNet 특징을 그대로 사용할 수 있어 보이는 영역
- MNIST에 맞게 재학습이 필요해 보이는 영역

동결 정책은 반드시 연속적이어야 한다.

예:
conv1, bn1, layer1, layer2 동결
layer3, layer4 학습

처럼 앞쪽은 동결하고 뒤쪽은 학습한다.

6개 레이어는 반드시
freeze_layers 또는 train_layers 중 하나에
정확히 한 번씩 포함되어야 한다.

boundary_layer에는
재학습을 시작하는 첫 번째 레이어를 넣어라.

중요:
이 판단은 feature map 이미지 한 장을 기반으로 한
휴리스틱 분석이므로 확정적인 결론인 것처럼 말하지 마라.

confidence는 0부터 1 사이의 값으로 표현하라.
"""


response = client.responses.parse(
    model="gpt-6-astra",

    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": prompt
                },
                {
                    "type": "input_image",
                    "image_url":
                        f"data:image/png;base64,{image_base64}",
                    "detail": "original"
                }
            ]
        }
    ],

    text_format=FreezePlan
)


plan = response.output_parsed


# =========================
# 7. 결과 검증
# =========================
ALL_LAYERS = {
    "conv1",
    "bn1",
    "layer1",
    "layer2",
    "layer3",
    "layer4"
}

freeze_set = set(plan.freeze_layers)
train_set = set(plan.train_layers)


# 동결/학습 중복 확인
if freeze_set & train_set:
    raise ValueError(
        f"동결과 학습에 동시에 포함된 레이어가 있습니다: "
        f"{freeze_set & train_set}"
    )


# 빠진 레이어 확인
if freeze_set | train_set != ALL_LAYERS:
    raise ValueError(
        "GPT 결과에 누락된 레이어가 있습니다."
    )


# confidence 범위 확인
if not 0 <= plan.confidence <= 1:
    raise ValueError(
        "confidence 값이 0~1 범위를 벗어났습니다."
    )


# =========================
# 8. JSON 저장
# =========================
result = plan.model_dump()

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        result,
        f,
        ensure_ascii=False,
        indent=2
    )


# =========================
# 9. 화면 출력
# =========================
print()
print("===== GPT 분석 결과 =====")

print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    )
)

print()
print(
    "JSON 저장 완료:",
    OUTPUT_PATH
)