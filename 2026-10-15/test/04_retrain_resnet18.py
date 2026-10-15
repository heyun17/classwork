import json
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from torchvision.models import resnet18, ResNet18_Weights


# =========================================================
# 1. 경로 / 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parent

FREEZE_PLAN_PATH = BASE_DIR / "freeze_plan.json"

# 1번에서 다운로드한 MNIST가
# classwork/data에 있으므로 상위 폴더 사용
DATA_DIR = BASE_DIR.parent / "data"

MODEL_PATH = BASE_DIR / "resnet18_mnist_best.pth"

EPOCHS = 2
BATCH_SIZE = 64

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)

print("사용 장치:", DEVICE)


# =========================================================
# 2. GPT 동결 계획 읽기
# =========================================================
with open(
    FREEZE_PLAN_PATH,
    "r",
    encoding="utf-8"
) as f:
    plan = json.load(f)


freeze_layers = plan["freeze_layers"]
train_layers = plan["train_layers"]


print()
print("===== GPT 동결 계획 =====")
print("동결:", freeze_layers)
print("재학습:", train_layers)
print("재학습 시작:", plan["boundary_layer"])


# =========================================================
# 3. MNIST 전처리
# =========================================================
weights = ResNet18_Weights.DEFAULT


# MNIST는 흑백 1채널
# ResNet18은 RGB 3채널 입력이므로 3채널로 변환
transform = transforms.Compose([
    transforms.Grayscale(
        num_output_channels=3
    ),

    weights.transforms()
])


# =========================================================
# 4. MNIST 데이터
# =========================================================
train_dataset = datasets.MNIST(
    root=DATA_DIR,
    train=True,
    download=True,
    transform=transform
)


test_dataset = datasets.MNIST(
    root=DATA_DIR,
    train=False,
    download=True,
    transform=transform
)


# 실습용으로 일부 데이터만 사용
train_dataset = Subset(train_dataset, range(6000))
test_dataset = Subset(test_dataset, range(1000))


train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)


test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


print()
print("Train:", len(train_dataset))
print("Test :", len(test_dataset))


# =========================================================
# 5. ImageNet pretrained ResNet18
# =========================================================
model = resnet18(
    weights=weights
)


# ImageNet은 1000개 클래스
# MNIST는 0~9 = 10개 클래스
model.fc = nn.Linear(
    model.fc.in_features,
    10
)


# =========================================================
# 6. 일단 전체 동결
# =========================================================
for param in model.parameters():
    param.requires_grad = False


# =========================================================
# 7. GPT가 train으로 선택한 레이어만 해제
# =========================================================
for layer_name in train_layers:

    layer = getattr(
        model,
        layer_name
    )

    for param in layer.parameters():
        param.requires_grad = True


# =========================================================
# 8. FC는 항상 학습
# =========================================================
for param in model.fc.parameters():
    param.requires_grad = True


# =========================================================
# 9. 실제 학습 상태 확인
# =========================================================
print()
print("===== 레이어 상태 =====")

for name in [
    "conv1",
    "bn1",
    "layer1",
    "layer2",
    "layer3",
    "layer4"
]:

    layer = getattr(model, name)

    trainable = any(
        p.requires_grad
        for p in layer.parameters()
    )

    print(
        f"{name:8s} : "
        f"{'TRAIN' if trainable else 'FREEZE'}"
    )

print("fc       : TRAIN")


# =========================================================
# 10. 동결된 BatchNorm 통계도 고정
# =========================================================
def freeze_bn_statistics():

    for layer_name in freeze_layers:

        layer = getattr(
            model,
            layer_name
        )

        for module in layer.modules():

            if isinstance(
                module,
                nn.BatchNorm2d
            ):
                module.eval()


# =========================================================
# 11. GPU / CPU로 이동
# =========================================================
model = model.to(DEVICE)


# =========================================================
# 12. Loss
# =========================================================
criterion = nn.CrossEntropyLoss()


# =========================================================
# 13. Optimizer
# =========================================================

# GPT가 재학습하라고 한 pretrained layer
backbone_params = []

for layer_name in train_layers:

    layer = getattr(
        model,
        layer_name
    )

    backbone_params.extend(
        layer.parameters()
    )


# pretrained layer는 작은 learning rate
# 새 fc는 큰 learning rate
optimizer = optim.Adam([
    {
        "params": backbone_params,
        "lr": 0.0001
    },
    {
        "params": model.fc.parameters(),
        "lr": 0.001
    }
])


# =========================================================
# 14. 학습
# =========================================================
best_accuracy = 0.0


for epoch in range(EPOCHS):

    # -------------------------
    # TRAIN
    # -------------------------
    model.train()

    # model.train() 하면 BN도 train으로 바뀌므로
    # 동결된 BN만 다시 eval
    freeze_bn_statistics()

    train_loss = 0.0
    train_correct = 0
    train_total = 0


    for images, labels in train_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            labels
        )

        loss.backward()

        optimizer.step()


        train_loss += (
            loss.item()
            * images.size(0)
        )

        predictions = outputs.argmax(
            dim=1
        )

        train_correct += (
            predictions == labels
        ).sum().item()

        train_total += labels.size(0)


    train_loss /= train_total

    train_accuracy = (
        train_correct
        / train_total
    )


    # -------------------------
    # TEST / VALIDATION
    # -------------------------
    model.eval()

    test_correct = 0
    test_total = 0


    with torch.no_grad():

        for images, labels in test_loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)

            predictions = outputs.argmax(
                dim=1
            )

            test_correct += (
                predictions == labels
            ).sum().item()

            test_total += labels.size(0)


    test_accuracy = (
        test_correct
        / test_total
    )


    print()
    print(
        f"Epoch {epoch + 1}/{EPOCHS}"
    )

    print(
        f"Train Loss     : "
        f"{train_loss:.4f}"
    )

    print(
        f"Train Accuracy : "
        f"{train_accuracy:.4f}"
    )

    print(
        f"Test Accuracy  : "
        f"{test_accuracy:.4f}"
    )


    # -------------------------
    # 최고 모델 저장
    # -------------------------
    if test_accuracy > best_accuracy:

        best_accuracy = test_accuracy

        torch.save(
            model.state_dict(),
            MODEL_PATH
        )

        print(
            "→ 최고 모델 저장:",
            MODEL_PATH.name
        )


# =========================================================
# 15. 최종 결과
# =========================================================
print()
print("==============================")
print("재학습 완료")
print("==============================")

print(
    f"Best Test Accuracy: "
    f"{best_accuracy:.4f}"
)

print(
    "저장 모델:",
    MODEL_PATH
)