from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt

from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from torchvision.models import resnet18, ResNet18_Weights

from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
    classification_report
)


# =========================================================
# 1. 경로 / 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR.parent / "data"

MODEL_PATH = (
    BASE_DIR / "resnet18_mnist_best.pth"
)

CONFUSION_PATH = (
    BASE_DIR / "confusion_matrix.png"
)

GRADCAM_PATH = (
    BASE_DIR / "gradcam_mnist.png"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)

print("사용 장치:", DEVICE)


# =========================================================
# 2. 학습 때 사용한 것과 동일한 전처리
# =========================================================
weights = ResNet18_Weights.DEFAULT

transform = transforms.Compose([
    transforms.Grayscale(
        num_output_channels=3
    ),
    weights.transforms()
])


# =========================================================
# 3. Test 데이터
# =========================================================
test_dataset = datasets.MNIST(
    root=DATA_DIR,
    train=False,
    download=True,
    transform=transform
)

# 4번과 동일하게 1000장 사용
test_dataset = Subset(
    test_dataset,
    range(1000)
)

test_loader = DataLoader(
    test_dataset,
    batch_size=64,
    shuffle=False,
    num_workers=0
)


# Grad-CAM 화면 표시용 원본 MNIST
raw_test_dataset = datasets.MNIST(
    root=DATA_DIR,
    train=False,
    download=True
)


# =========================================================
# 4. ResNet18 구조 복원
# =========================================================
model = resnet18(
    weights=None
)

# MNIST 10개 클래스
model.fc = nn.Linear(
    model.fc.in_features,
    10
)


# =========================================================
# 5. 4번에서 저장한 state_dict 불러오기
# =========================================================
model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=True
    )
)

model = model.to(DEVICE)

model.eval()

print("모델 불러오기 완료")


# =========================================================
# 6. 전체 Test 예측
# =========================================================
all_labels = []
all_predictions = []


with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        outputs = model(images)

        predictions = outputs.argmax(
            dim=1
        )

        all_labels.extend(
            labels.cpu().numpy()
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )


# =========================================================
# 7. 혼동행렬 계산
# =========================================================
cm = confusion_matrix(
    all_labels,
    all_predictions
)


disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=list(range(10))
)

fig, ax = plt.subplots(
    figsize=(9, 9)
)

disp.plot(
    ax=ax,
    cmap="Blues",
    values_format="d",
    colorbar=False
)

plt.title(
    "ResNet18 MNIST Confusion Matrix"
)

plt.tight_layout()

plt.savefig(
    CONFUSION_PATH,
    dpi=200
)

print()
print(
    "혼동행렬 저장 완료:",
    CONFUSION_PATH
)


# =========================================================
# 8. 숫자별 Precision / Recall / F1
# =========================================================
print()
print("===== Classification Report =====")

print(
    classification_report(
        all_labels,
        all_predictions,
        digits=4
    )
)


# =========================================================
# 9. Grad-CAM
# =========================================================
class GradCAM:

    def __init__(
        self,
        model,
        target_layer
    ):

        self.model = model

        self.target_layer = target_layer

        self.activations = None
        self.gradients = None

        self.hook = (
            target_layer.register_forward_hook(
                self.save_activation
            )
        )


    def save_activation(
        self,
        module,
        input,
        output
    ):

        self.activations = output

        output.register_hook(
            self.save_gradient
        )


    def save_gradient(
        self,
        grad
    ):

        self.gradients = grad


    def generate(
        self,
        x,
        class_index=None
    ):

        self.model.zero_grad()

        output = self.model(x)


        # class 지정 안 하면
        # 모델이 예측한 숫자를 사용
        if class_index is None:

            class_index = (
                output.argmax(dim=1).item()
            )


        score = output[
            0,
            class_index
        ]


        score.backward()


        # 각 채널 gradient 평균
        weights = (
            self.gradients.mean(
                dim=(2, 3),
                keepdim=True
            )
        )


        # weighted feature maps
        cam = (
            weights
            * self.activations
        ).sum(
            dim=1,
            keepdim=True
        )


        # 음수 제거
        cam = F.relu(cam)


        # 입력 이미지 크기로 확대
        cam = F.interpolate(
            cam,
            size=x.shape[2:],
            mode="bilinear",
            align_corners=False
        )


        # 0 ~ 1
        cam = cam[0, 0]

        cam = (
            cam - cam.min()
        ) / (
            cam.max()
            - cam.min()
            + 1e-8
        )


        return (
            cam.detach().cpu().numpy(),
            class_index
        )


# =========================================================
# 10. Grad-CAM 대상 레이어
# =========================================================

# ResNet18의 마지막 convolution
target_layer = (
    model.layer4[-1].conv2
)

gradcam = GradCAM(
    model,
    target_layer
)


# =========================================================
# 11. MNIST 샘플 하나 선택
# =========================================================
sample_index = 0

image_tensor, answer = (
    test_dataset[sample_index]
)

x = (
    image_tensor
    .unsqueeze(0)
    .to(DEVICE)
)


# =========================================================
# 12. Grad-CAM 생성
# =========================================================
cam, prediction = (
    gradcam.generate(x)
)


# =========================================================
# 13. 원본 이미지
# =========================================================
original_image, _ = (
    raw_test_dataset[
        sample_index
    ]
)

original = np.array(
    original_image
)


# CAM을 28 x 28로 변경
cam_tensor = torch.tensor(
    cam
).unsqueeze(0).unsqueeze(0)

cam_28 = F.interpolate(
    cam_tensor,
    size=(28, 28),
    mode="bilinear",
    align_corners=False
)

cam_28 = (
    cam_28[0, 0]
    .numpy()
)


# =========================================================
# 14. XAI 결과 시각화
# =========================================================
fig, axes = plt.subplots(
    1,
    3,
    figsize=(10, 3)
)


# 원본
axes[0].imshow(
    original,
    cmap="gray"
)

axes[0].set_title(
    f"Original\nAnswer: {answer}"
)

axes[0].axis("off")


# Grad-CAM
axes[1].imshow(
    cam_28,
    cmap="jet"
)

axes[1].set_title(
    "Grad-CAM"
)

axes[1].axis("off")


# Overlay
axes[2].imshow(
    original,
    cmap="gray"
)

axes[2].imshow(
    cam_28,
    cmap="jet",
    alpha=0.5
)

axes[2].set_title(
    f"Prediction: {prediction}"
)

axes[2].axis("off")


plt.tight_layout()

plt.savefig(
    GRADCAM_PATH,
    dpi=200,
    bbox_inches="tight"
)

print()
print(
    "Grad-CAM 저장 완료:",
    GRADCAM_PATH
)

print(
    "실제 숫자:",
    answer
)

print(
    "예측 숫자:",
    prediction
)


# =========================================================
# 15. 결과 화면
# =========================================================
plt.show()