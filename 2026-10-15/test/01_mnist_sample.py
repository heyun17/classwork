from torchvision import datasets
import matplotlib.pyplot as plt


# =========================
# 1. MNIST 다운로드
# =========================
mnist = datasets.MNIST(
    root="./data",
    train=True,
    download=True
)


# =========================
# 2. 샘플 1개 가져오기
# =========================
image, label = mnist[0]


# =========================
# 3. 이미지 저장
# =========================
image.save("mnist_sample.png")

print("이미지 저장 완료: mnist_sample.png")
print("정답 숫자:", label)


# =========================
# 4. 화면 출력
# =========================
plt.imshow(image, cmap="gray")
plt.title(f"MNIST Label: {label}")
plt.axis("off")
plt.show()