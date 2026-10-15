from torchvision.models import resnet18, ResNet18_Weights

# pretrained ResNet18
model = resnet18(weights=ResNet18_Weights.DEFAULT)


# 1. 전체 레이어 동결
for param in model.parameters():
    param.requires_grad = False


# 2. layer4만 학습 가능하게 변경
for param in model.layer4.parameters():
    param.requires_grad = True