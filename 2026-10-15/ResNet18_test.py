import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from PIL import Image
from torchvision.models import resnet18, ResNet18_Weights
from torchvision.utils import make_grid


# =========================
# 1. ResNet18
# =========================
weights = ResNet18_Weights.DEFAULT

model = resnet18(weights=weights)
model.eval()


# =========================
# 2. 이미지
# =========================
img = Image.open("image.jpg").convert("RGB")

transform = weights.transforms()

x = transform(img).unsqueeze(0)


# =========================
# 3. Feature Map 수집
# =========================
all_maps = []

layer_names = []
layer_shapes = []

padding = 2
map_size = 112
num_channels = 10


with torch.no_grad():

    for name, layer in model.named_children():

        # avgpool, fc 제외
        if name in ["avgpool", "fc"]:
            break

        x = layer(x)

        print(f"{name}: {x.shape}")

        layer_names.append(name)
        layer_shapes.append(x.shape)

        # 앞의 10개 채널
        fmap = x[0, :num_channels]

        # 모든 feature map을 112 x 112로 통일
        fmap = F.interpolate(
            fmap.unsqueeze(1),
            size=(map_size, map_size),
            mode="bilinear",
            align_corners=False
        )

        # 각각 0~1 정규화
        for j in range(fmap.shape[0]):

            f = fmap[j]

            f = (f - f.min()) / (
                f.max() - f.min() + 1e-8
            )

            all_maps.append(f)


# =========================
# 4. 하나의 Grid 생성
# =========================
all_maps = torch.stack(all_maps)

grid = make_grid(
    all_maps,
    nrow=num_channels,
    padding=padding
)


# =========================
# 5. 한 Plot에 출력
# =========================
fig, ax = plt.subplots(figsize=(17, 12))

ax.imshow(
    grid[0].cpu().numpy(),
    cmap="gray"
)


# =========================
# 6. 레이어 이름 표시
# =========================
for i, (name, shape) in enumerate(
    zip(layer_names, layer_shapes)
):

    y = padding + i * (map_size + padding) + map_size / 2

    label = (
        f"{name}\n"
        f"{shape[1]}×{shape[2]}×{shape[3]}"
    )

    ax.text(
        -10,
        y,
        label,
        ha="right",
        va="center",
        fontsize=9,
        clip_on=False
    )


ax.set_title(
    "ResNet18 Feature Maps",
    fontsize=16
)

ax.axis("off")

# 왼쪽에 레이어 이름 들어갈 공간 확보
plt.subplots_adjust(left=0.16)

plt.show()