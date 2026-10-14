# alexnet
import torch
from torchvision import models, transforms
from PIL import Image

import matplotlib.pyplot as plt

# 1. 사전학습된 AlexNet 불러오기
model = models.alexnet(weights="IMAGENET1K_V1")
model.eval()

# 2. 전처리 파이프라인 (ImageNet 규격)
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],   # ImageNet 평균
        std=[0.229, 0.224, 0.225]     # ImageNet 표준편차
    ),
])


# 3. 예시 이미지 불러오기 (로컬 파일도 가능)
img_list=["content/사람1.jpg","content/사람2.jpg","content/사람3.jpg","content/건물.jpg"]
for imgfile in img_list:
  img = Image.open(imgfile)   
  x = preprocess(img).unsqueeze(0)   
  print(x.shape) # 모델에서 요구하는 1, 3,224,224

  # 4. 추론
  with torch.no_grad():
      outputs = model(x)
      print('-'*100)
      print(outputs.max(0))
      #_, predicted = outputs.max(1)

  
  #print("\n ->예측된 클래스번호:", predicted.item())
  #print(" ->예측된 클래스:", classes[predicted.item()])
  #plt.figure(figsize=(3,3))
  #plt.axis('off')   # x, y 축 모두 숨김
  #plt.imshow(img)
  #plt.show()
