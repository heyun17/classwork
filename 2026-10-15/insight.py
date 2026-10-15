import os
import base64

from dotenv import load_dotenv
from openai import OpenAI


# .env 읽기
load_dotenv()

# 환경변수에서 API Key 읽기
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY가 .env에 없습니다.")

client = OpenAI(api_key=api_key)


IMAGE_PATH = "resnet_feature_maps.png"


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


image_base64 = encode_image(IMAGE_PATH)


prompt = """
이 이미지는 ResNet18의 레이어별 feature map 시각화 결과다.

다음 관점에서 분석해라.

1. conv1 ~ layer4까지 feature map 변화
2. 활성화 영역의 밀도
3. 특징의 다양성
4. 공간 정보가 유지되는 정도
5. 깊은 레이어에서 특징이 추상화되는 정도
6. 전이학습 관점에서 동결 후보 레이어
7. fine-tuning 후보 레이어
8. 이미지 시각화만으로 판단할 때의 한계

출력 형식:

[관찰]
...

[주요 변화 지점]
...

[동결 후보]
...

[Fine-tuning 후보]
...

[주의점]
...
"""


response = client.responses.create(
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
                    "image_url": f"data:image/png;base64,{image_base64}",
                    "detail": "high"
                }
            ]
        }
    ]
)

print(response.output_text)