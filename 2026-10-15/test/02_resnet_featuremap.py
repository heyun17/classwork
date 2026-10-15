import torch
import matplotlib.pyplot as plt

from PIL import Image
from torchvision.models import resnet18, ResNet18_Weights


# =========================
# 1. pretrained ResNet18
# =========================
weights = ResNet18_Weights.DEFAULT

model = resnet18(weights=weights)
model.eval()


# =========================
# 2. MNIST 샘플 이미지
# =========================
image = Image.open("mnist_sample.png").convert("RGB")

transform = weights.transforms()

x = transform(image).unsqueeze(0)


# =========================
# 3. Feature Map 저장
# =========================
feature_maps = []
layer_names = []
layer_shapes = []


with torch.no_grad():

    for name, layer in model.named_children():

        # avgpool, fc 전까지만
        if name in ["avgpool", "fc"]:
            break

        x = layer(x)

        feature_maps.append(x.clone())
        layer_names.append(name)
        layer_shapes.append(x.shape)

        print(
            f"{name:10s} -> {tuple(x.shape)}"
        )


# =========================
# 4. 한 Figure에 시각화
# =========================
num_channels = 10
num_layers = len(feature_maps)

fig, axes = plt.subplots(
    num_layers,
    num_channels,
    figsize=(16, 12)
)


for row, feature in enumerate(feature_maps):

    channels = min(
        num_channels,
        feature.shape[1]
    )

    for col in range(num_channels):

        ax = axes[row, col]

        if col < channels:

            fmap = (
                feature[0, col]
                .cpu()
                .numpy()
            )

            ax.imshow(
                fmap,
                cmap="gray"
            )

        ax.axis("off")


    # 레이어 이름 직접 표시
    axes[row, 0].text(
        -0.15,
        0.5,
        f"{layer_names[row]}\n"
        f"{layer_shapes[row][1]}×"
        f"{layer_shapes[row][2]}×"
        f"{layer_shapes[row][3]}",
        transform=axes[row, 0].transAxes,
        ha="right",
        va="center",
        fontsize=9
    )


fig.suptitle(
    "ResNet18 Feature Maps - MNIST Sample",
    fontsize=16
)

# 왼쪽 레이어 이름 공간
plt.subplots_adjust(
    left=0.13,
    top=0.94,
    hspace=0.15,
    wspace=0.03
)

plt.savefig(
    "resnet18_feature_maps.png",
    dpi=200,
    bbox_inches="tight"
)

print()
print("저장 완료: resnet18_feature_maps.png")

plt.show()