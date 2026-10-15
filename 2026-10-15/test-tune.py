###########################################
## 튜닝할 위치 확인
###########################################
import torch
import matplotlib.pyplot as plt
from torchvision import models, transforms
import torch.nn.functional as F

from PIL import Image
testing = Image.open("image.jpg")

# 1. 모델 준비 (ResNet18, ImageNet 가중치)
model = models.resnet18(weights="IMAGENET1K_V1")
model.eval()

# 2. ImageNet 전처리 (Tensor용)
transform = transforms.Compose([
    # transforms.Lambda(lambda img: img.permute(2,0,1)),  # HWC → CHW
    transforms.Resize((224,224)),                       # 32x32 → 224x224
    transforms.ToTensor(),                              # [0,255] → [0,1]
    transforms.Normalize([0.485,0.456,0.406],
                         [0.229,0.224,0.225])
])

# 3. testimg 준비 (torch.Size([32,32,3]), 값 범위 0~1)
x = transform(testing).unsqueeze(0)   # [1, 3, 224, 224]

# 4. 중간 레이어 feature map 추출 & 시각화
layers = dict(model.named_children())

def show_feature(name, out, max_channels=8):
    fmap = out.squeeze(0).detach().cpu()
    num = min(max_channels, fmap.shape[0])
    fig, axes = plt.subplots(1, num, figsize=(15,4))

    for i, ax in enumerate(axes if num>1 else [axes]):
        ax.imshow(fmap[i], cmap="gray")
        ax.axis("off")

    axes[0].set_title(f"{name} → {tuple(out.shape)}", fontsize=10, loc="left")
    plt.show()

out = x
for name in ["conv1", "layer1", "layer2","layer3","layer4"]:
    out = layers[name](out)
    show_feature(name, out)
