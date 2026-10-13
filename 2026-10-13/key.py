import requests
from PIL import Image
from io import BytesIO
import cv2
import matplotlib.pyplot as plt

# 인터넷 이미지 로드
url = 'https://m.health.chosun.com/site/data/img_dir/2013/06/26/2013062602051_5.jpg'
response = requests.get(url)
img = Image.open(BytesIO(response.content)).convert('RGB')

# 임시 저장 후 추론
img.save('test_pose.jpg')
results = model('test_pose.jpg', verbose=False, save=True)

# 키포인트 시각화
annotated = cv2.cvtColor(results[0].plot(), cv2.COLOR_BGR2RGB)
plt.figure(figsize=(10, 8))
plt.imshow(annotated)
plt.title('YOLOv8-Pose 17개 키포인트')
plt.axis('off')
plt.show()

# 키포인트 좌표 출력
if results[0].keypoints is not None:
    for person_idx, kpts in enumerate(results[0].keypoints.xy.cpu().numpy()):
        print(f'\n사람 {person_idx + 1} 키포인트 좌표 (x, y)')
        print('-' * 35)
        for i, (name, (x, y)) in enumerate(zip(KEYPOINT_NAMES, kpts)):
            print(f'  [{i:2d}] {name:<6}: ({x:6.1f}, {y:6.1f})')

