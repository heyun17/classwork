import os
import tkinter as tk

import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image, ImageDraw
from torchvision import datasets, transforms
from torch.utils.data import DataLoader


# =========================
# 1. CNN 모델
# =========================
class CNN(nn.Module):
    def __init__(self):
        super().__init__()

        self.conv1 = nn.Conv2d(1, 8, 3, padding=1)
        self.conv2 = nn.Conv2d(8, 16, 3, padding=1)
        self.conv3 = nn.Conv2d(16, 32, 3, padding=1)

        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(2, 2)

        self.fc = nn.Linear(32 * 3 * 3, 10)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))   # 28 -> 14
        x = self.pool(self.relu(self.conv2(x)))   # 14 -> 7
        x = self.pool(self.relu(self.conv3(x)))   # 7 -> 3

        x = torch.flatten(x, 1)
        x = self.fc(x)

        return x


# =========================
# 2. 모델 생성
# =========================
model = CNN()

MODEL_PATH = "mnist_cnn.pth"


# =========================
# 3. 저장된 모델이 없으면 학습
# =========================
if not os.path.exists(MODEL_PATH):

    print("저장된 모델 없음 -> MNIST 학습 시작")

    transform = transforms.ToTensor()

    train_data = datasets.MNIST(
        root="./data",
        train=True,
        download=True,
        transform=transform
    )

    train_loader = DataLoader(
        train_data,
        batch_size=64,
        shuffle=True
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(5):

        for x, y in train_loader:

            optimizer.zero_grad()

            output = model(x)
            loss = criterion(output, y)

            loss.backward()
            optimizer.step()

        print(
            f"epoch: {epoch + 1}, "
            f"loss: {loss.item():.4f}"
        )

    # state_dict 저장
    torch.save(model.state_dict(), MODEL_PATH)

    print("모델 저장 완료:", MODEL_PATH)


# =========================
# 4. 저장된 모델 불러오기
# =========================
else:
    print("저장된 모델 발견 -> 학습 생략")


model.load_state_dict(
    torch.load(MODEL_PATH, weights_only=True)
)

model.eval()


# =========================
# 5. 손글씨 입력용 창
# =========================
root = tk.Tk()
root.title("MNIST 손글씨 숫자 인식")


canvas = tk.Canvas(
    root,
    width=280,
    height=280,
    bg="black"
)

canvas.pack()


# 실제 추론에 사용할 PIL 이미지
image = Image.new(
    "L",
    (280, 280),
    0
)

draw = ImageDraw.Draw(image)


# =========================
# 6. 마우스로 숫자 그리기
# =========================
def paint(event):

    x = event.x
    y = event.y

    r = 10

    canvas.create_oval(
        x - r,
        y - r,
        x + r,
        y + r,
        fill="white",
        outline="white"
    )

    draw.ellipse(
        (
            x - r,
            y - r,
            x + r,
            y + r
        ),
        fill=255
    )


canvas.bind("<B1-Motion>", paint)


# =========================
# 7. 추론
# =========================
def predict():

    transform = transforms.Compose([
        transforms.Resize((28, 28)),
        transforms.ToTensor()
    ])

    x = transform(image)

    # (1, 28, 28)
    # ->
    # (1, 1, 28, 28)
    x = x.unsqueeze(0)

    with torch.no_grad():

        output = model(x)

        pred = output.argmax(dim=1)

    result_label.config(
        text=f"예측 숫자: {pred.item()}"
    )


# =========================
# 8. 화면 지우기
# =========================
def clear():

    canvas.delete("all")

    draw.rectangle(
        (0, 0, 280, 280),
        fill=0
    )

    result_label.config(
        text="예측 숫자:"
    )


# =========================
# 9. 버튼
# =========================
predict_button = tk.Button(
    root,
    text="추론",
    command=predict
)

predict_button.pack()


clear_button = tk.Button(
    root,
    text="지우기",
    command=clear
)

clear_button.pack()


result_label = tk.Label(
    root,
    text="예측 숫자:",
    font=("Arial", 20)
)

result_label.pack()


# =========================
# 10. GUI 실행
# =========================
root.mainloop()