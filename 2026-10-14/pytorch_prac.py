import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import (
    TensorDataset,
    DataLoader,
    random_split
)

import matplotlib.pyplot as plt


# ============================================================
# 1. 랜덤 시드 고정
#
# 실행할 때마다 데이터 분할과 초기 Weight가
# 달라지는 것을 방지
# ============================================================

torch.manual_seed(42)


# ============================================================
# 2. 데이터 생성
#
# 입력:
# x1, x2, x3
#
# 출력:
# y = 0 또는 1
#
# 데이터 300개 생성
# ============================================================

X = torch.randint(
    0,
    2,
    (300, 3)
).float()


# ------------------------------------------------------------
# 예제 정답 규칙
#
# x1 + x2 + x3 중
# 2개 이상이 1이면 y = 1
#
# 아니면 y = 0
# ------------------------------------------------------------

y = (
    X.sum(dim=1) >= 2
).float().unsqueeze(1)


print("X shape:", X.shape)
print("y shape:", y.shape)


# ============================================================
# 3. TensorDataset 생성
# ============================================================

dataset = TensorDataset(
    X,
    y
)


# ============================================================
# 4. Train / Validation / Test 분리
#
# 전체 300개
#
# Train      : 70% = 210개
# Validation : 15% = 45개
# Test       : 15% = 45개
# ============================================================

train_size = 210
val_size = 45
test_size = 45


train_dataset, val_dataset, test_dataset = random_split(

    dataset,

    [
        train_size,
        val_size,
        test_size
    ]
)


print("\n===== 데이터 분할 =====")

print(
    "Train:",
    len(train_dataset)
)

print(
    "Validation:",
    len(val_dataset)
)

print(
    "Test:",
    len(test_dataset)
)


# ============================================================
# 5. DataLoader
#
# Batch Size = 20
#
# 훈련 데이터는 shuffle=True
# 검증/테스트 데이터는 섞을 필요 없음
# ============================================================

batch_size = 20


train_loader = DataLoader(
    train_dataset,
    batch_size=batch_size,
    shuffle=True
)


val_loader = DataLoader(
    val_dataset,
    batch_size=batch_size,
    shuffle=False
)


test_loader = DataLoader(
    test_dataset,
    batch_size=batch_size,
    shuffle=False
)


# ============================================================
# 6. 모델 정의
#
# 입력        : 3
# Hidden 1    : 8
# Hidden 2    : 4
# 출력        : 1
#
# 구조:
#
# 3 → 8 → 4 → 1
# ============================================================

model = nn.Sequential(

    nn.Linear(3, 8),

    nn.ReLU(),

    nn.Linear(8, 4),

    nn.ReLU(),

    nn.Linear(4, 1)
)


print("\n===== 모델 구조 =====")

print(model)


# ============================================================
# 7. 파라미터 출력
# ============================================================

print("\n===== 모델 파라미터 =====")


total_params = 0


for name, param in model.named_parameters():

    count = param.numel()

    total_params += count

    print(
        f"{name:10s} "
        f"shape={tuple(param.shape)} "
        f"count={count}"
    )


print(
    "\n전체 파라미터 개수:",
    total_params
)


# ============================================================
# 8. Loss 함수
#
# 이진분류이므로 BCEWithLogitsLoss 사용
#
# 내부적으로 Sigmoid까지 포함
# ============================================================

criterion = nn.BCEWithLogitsLoss()


# ============================================================
# 9. Optimizer
#
# SGD 경사하강법
# ============================================================

optimizer = optim.SGD(

    model.parameters(),

    lr=0.1
)


# ============================================================
# 10. Early Stopping 설정
# ============================================================

# 최대 학습 횟수
max_epochs = 500


# Validation Loss가 몇 epoch 동안 개선되지 않으면
# 학습을 중단할 것인지
patience = 30


# 이 값보다 작게 좋아진 것은
# "개선"으로 인정하지 않음
min_delta = 0.0001


# 지금까지 가장 작은 Validation Loss
best_val_loss = float("inf")


# Validation Loss가 개선되지 않은 횟수
no_improvement_count = 0


# Best Model 저장 파일
best_model_path = "best_model.pt"


# 그래프용 Loss 기록
train_loss_history = []

val_loss_history = []


# ============================================================
# 11. 학습 시작
# ============================================================

for epoch in range(max_epochs):


    # ========================================================
    # TRAIN
    # ========================================================

    model.train()


    train_loss_sum = 0.0


    for batch_X, batch_y in train_loader:


        # ----------------------------------------------------
        # 1. 예측
        # ----------------------------------------------------

        logits = model(
            batch_X
        )


        # ----------------------------------------------------
        # 2. Loss 계산
        # ----------------------------------------------------

        loss = criterion(
            logits,
            batch_y
        )


        # ----------------------------------------------------
        # 3. 기존 Gradient 초기화
        # ----------------------------------------------------

        optimizer.zero_grad()


        # ----------------------------------------------------
        # 4. 역전파
        # ----------------------------------------------------

        loss.backward()


        # ----------------------------------------------------
        # 5. Weight / Bias 업데이트
        # ----------------------------------------------------

        optimizer.step()


        # ----------------------------------------------------
        # 현재 Batch의 Loss 누적
        # ----------------------------------------------------

        train_loss_sum += (
            loss.item()
            *
            batch_X.size(0)
        )


    # --------------------------------------------------------
    # 전체 Train 데이터의 평균 Loss
    # --------------------------------------------------------

    train_loss = (
        train_loss_sum
        /
        len(train_dataset)
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    model.eval()


    val_loss_sum = 0.0


    # Validation에서는
    # Gradient 계산 필요 없음
    with torch.no_grad():


        for batch_X, batch_y in val_loader:


            # 예측
            logits = model(
                batch_X
            )


            # Loss
            loss = criterion(
                logits,
                batch_y
            )


            val_loss_sum += (
                loss.item()
                *
                batch_X.size(0)
            )


    # --------------------------------------------------------
    # 전체 Validation 평균 Loss
    # --------------------------------------------------------

    val_loss = (
        val_loss_sum
        /
        len(val_dataset)
    )


    # ========================================================
    # 12. Epoch별 Loss 저장
    # ========================================================

    train_loss_history.append(
        train_loss
    )

    val_loss_history.append(
        val_loss
    )


    # ========================================================
    # 13. 현재 결과 출력
    # ========================================================

    print(

        f"Epoch "
        f"{epoch + 1:3d} | "

        f"Train Loss: "
        f"{train_loss:.6f} | "

        f"Val Loss: "
        f"{val_loss:.6f}"
    )


    # ========================================================
    # 14. Best Model 저장
    #
    # Validation Loss가 기존 Best보다 충분히 작으면
    # 새로운 Best Model
    # ========================================================

    if val_loss < best_val_loss - min_delta:


        best_val_loss = val_loss


        # ----------------------------------------------------
        # 현재 모델의 Weight/Bias 저장
        # ----------------------------------------------------

        torch.save(
            model.state_dict(),
            best_model_path
        )


        print(
            f"   → Best Model 저장 "
            f"(Val Loss: {best_val_loss:.6f})"
        )


        # 개선되었으므로 다시 0
        no_improvement_count = 0


    else:


        # 개선되지 않음
        no_improvement_count += 1


        print(
            f"   → 개선 없음 "
            f"({no_improvement_count}/{patience})"
        )


    # ========================================================
    # 15. Early Stopping
    #
    # patience만큼 연속으로 Validation Loss가
    # 개선되지 않았다면 학습 종료
    # ========================================================

    if no_improvement_count >= patience:


        print("\n==============================")

        print(
            "Early Stopping!"
        )

        print(
            f"{patience} epoch 동안 "
            f"Validation Loss가 개선되지 않았습니다."
        )

        print("==============================")


        break


# ============================================================
# 16. 실제 학습된 Epoch 수
# ============================================================

trained_epochs = len(
    train_loss_history
)


print(
    "\n실제 학습 Epoch:",
    trained_epochs
)


print(
    "Best Validation Loss:",
    best_val_loss
)


# ============================================================
# 17. Train / Validation Loss 그래프
# ============================================================

plt.figure(
    figsize=(10, 5)
)


plt.plot(

    range(1, trained_epochs + 1),

    train_loss_history,

    label="Train Loss"
)


plt.plot(

    range(1, trained_epochs + 1),

    val_loss_history,

    label="Validation Loss"
)


plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Loss"
)

plt.title(
    "Train / Validation Loss"
)

plt.legend()

plt.grid(
    alpha=0.3
)

plt.show()


# ============================================================
# 18. Best Model 다시 불러오기
#
# 마지막 epoch 모델을 테스트하는 것이 아니라
# Validation Loss가 가장 좋았던 모델을 사용
# ============================================================

model.load_state_dict(

    torch.load(
        best_model_path,
        weights_only=True
    )
)


model.eval()


print(
    "\nBest Model 불러오기 완료"
)


# ============================================================
# 19. Test 데이터 평가
#
# Test 데이터는 학습 중에 사용하지 않는다.
#
# 마지막 최종 평가에서만 사용
# ============================================================

test_loss_sum = 0.0

correct = 0

total = 0


with torch.no_grad():


    for batch_X, batch_y in test_loader:


        # ----------------------------------------------------
        # 모델 출력
        # ----------------------------------------------------

        logits = model(
            batch_X
        )


        # ----------------------------------------------------
        # Test Loss
        # ----------------------------------------------------

        loss = criterion(
            logits,
            batch_y
        )


        test_loss_sum += (
            loss.item()
            *
            batch_X.size(0)
        )


        # ----------------------------------------------------
        # Logit → 확률
        # ----------------------------------------------------

        probabilities = torch.sigmoid(
            logits
        )


        # ----------------------------------------------------
        # 확률 >= 0.5 → 1
        # 확률 < 0.5 → 0
        # ----------------------------------------------------

        predictions = (
            probabilities >= 0.5
        ).float()


        # ----------------------------------------------------
        # 정확도 계산
        # ----------------------------------------------------

        correct += (
            predictions == batch_y
        ).sum().item()


        total += batch_y.size(0)


# ============================================================
# 20. 최종 Test 결과
# ============================================================

test_loss = (
    test_loss_sum
    /
    len(test_dataset)
)


test_accuracy = (
    correct
    /
    total
    *
    100
)


print("\n")
print("=" * 50)

print("TEST 결과")

print("=" * 50)


print(
    f"Test Loss: "
    f"{test_loss:.6f}"
)


print(
    f"Test Accuracy: "
    f"{test_accuracy:.2f}%"
)


# ============================================================
# 21. Best Model의 최종 Weight / Bias 확인
# ============================================================

print("\n===== Best Model 파라미터 =====")


for name, param in model.named_parameters():

    print(
        f"\n{name}"
    )

    print(
        param.data
    )