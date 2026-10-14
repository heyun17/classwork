import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button


# ============================================================
# 1. 학습용 데이터
#
# x가 작으면 0, x가 크면 1인 간단한 이진 분류 데이터
# ============================================================

x = np.array([
    0.5, 1.0, 1.5, 2.0,
    3.0, 3.5, 4.0, 4.5
])

y = np.array([
    0, 0, 0, 0,
    1, 1, 1, 1
])


# ============================================================
# 2. 시그모이드 함수
#
# z = wx + b
#
# 결과를 0~1 사이의 확률로 바꾼다.
# ============================================================

def sigmoid(z):
    return 1 / (1 + np.exp(-z))


# ============================================================
# 3. Binary Cross Entropy Loss
#
# 실제값과 예측 확률이 얼마나 다른지 측정
# ============================================================

def calculate_loss(y_true, y_pred):

    # log(0)이 발생하지 않도록 값 제한
    epsilon = 1e-7

    y_pred = np.clip(
        y_pred,
        epsilon,
        1 - epsilon
    )

    loss = -np.mean(
        y_true * np.log(y_pred)
        +
        (1 - y_true) * np.log(1 - y_pred)
    )

    return loss


# ============================================================
# 4. 경사하강법 1회
#
# 현재 w, b에서
# loss가 감소하는 방향을 계산하여 조금 이동
# ============================================================

def gradient_descent_step(w, b, lr):

    # --------------------------------------------
    # 순전파
    #
    # z = wx + b
    # --------------------------------------------

    z = w * x + b

    y_pred = sigmoid(z)


    # --------------------------------------------
    # gradient 계산
    #
    # dw = loss를 w로 미분
    # db = loss를 b로 미분
    # --------------------------------------------

    error = y_pred - y

    dw = np.mean(
        error * x
    )

    db = np.mean(
        error
    )


    # --------------------------------------------
    # 경사하강
    #
    # 새로운 값 =
    # 현재 값 - learning rate × gradient
    # --------------------------------------------

    w = w - lr * dw

    b = b - lr * db

    return w, b


# ============================================================
# 5. 초기 값
# ============================================================

current_w = 0.0
current_b = 0.0
current_epoch = 0

loss_history = []


# ============================================================
# 6. 그래프 생성
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    1,
    2,
    figsize=(12, 6)
)

# 아래쪽에 슬라이더 공간 확보
plt.subplots_adjust(
    bottom=0.32
)


# ============================================================
# 7. 그래프 업데이트 함수
# ============================================================

def update_graph():

    global current_w
    global current_b
    global current_epoch


    # --------------------------------------------
    # 현재 모델 예측
    # --------------------------------------------

    x_line = np.linspace(
        0,
        5,
        200
    )

    probability = sigmoid(
        current_w * x_line
        +
        current_b
    )


    # 현재 데이터에 대한 loss 계산
    y_pred = sigmoid(
        current_w * x
        +
        current_b
    )

    loss = calculate_loss(
        y,
        y_pred
    )


    # ========================================================
    # 왼쪽 그래프
    # ========================================================

    ax1.clear()


    # 실제 데이터
    ax1.scatter(
        x,
        y,
        s=80,
        label="Data"
    )


    # Logistic Regression의 sigmoid 곡선
    ax1.plot(
        x_line,
        probability,
        linewidth=3,
        label="Prediction"
    )


    # 분류 기준 0.5
    ax1.axhline(
        0.5,
        linestyle="--",
        alpha=0.5,
        label="Threshold = 0.5"
    )


    ax1.set_xlim(
        0,
        5
    )

    ax1.set_ylim(
        -0.1,
        1.1
    )

    ax1.set_xlabel(
        "x"
    )

    ax1.set_ylabel(
        "Probability"
    )


    ax1.set_title(
        f"Epoch : {current_epoch}\n"
        f"Weight : {current_w:.3f}   "
        f"Bias : {current_b:.3f}\n"
        f"Loss : {loss:.4f}"
    )

    ax1.legend()


    # ========================================================
    # 오른쪽 그래프 - Loss 변화
    # ========================================================

    ax2.clear()


    if len(loss_history) > 0:

        ax2.plot(
            range(len(loss_history)),
            loss_history,
            marker="o"
        )


    ax2.set_xlabel(
        "Gradient Descent Step"
    )

    ax2.set_ylabel(
        "Loss"
    )

    ax2.set_title(
        "Loss History"
    )

    ax2.grid(
        alpha=0.3
    )


    fig.canvas.draw_idle()


# ============================================================
# 8. Slider 생성
# ============================================================

# Weight 슬라이더 위치
weight_axis = plt.axes([
    0.15,
    0.20,
    0.65,
    0.03
])

weight_slider = Slider(
    weight_axis,
    "Weight",
    -5.0,
    5.0,
    valinit=0.0,
    valstep=0.1
)


# Bias 슬라이더
bias_axis = plt.axes([
    0.15,
    0.15,
    0.65,
    0.03
])

bias_slider = Slider(
    bias_axis,
    "Bias",
    -5.0,
    5.0,
    valinit=0.0,
    valstep=0.1
)


# Learning Rate 슬라이더
lr_axis = plt.axes([
    0.15,
    0.10,
    0.65,
    0.03
])

lr_slider = Slider(
    lr_axis,
    "Learning Rate",
    0.001,
    2.0,
    valinit=0.1
)


# ============================================================
# 9. Slider를 움직였을 때
#
# Weight와 Bias는 "초기값" 역할을 한다.
# 값을 바꾸면 학습 상태를 처음부터 다시 시작한다.
# ============================================================

def slider_changed(val):

    global current_w
    global current_b
    global current_epoch
    global loss_history

    current_w = weight_slider.val
    current_b = bias_slider.val

    current_epoch = 0

    loss_history = []

    update_graph()


weight_slider.on_changed(
    slider_changed
)

bias_slider.on_changed(
    slider_changed
)


# ============================================================
# 10. Gradient Descent 1회 실행
# ============================================================

def one_step(event):

    global current_w
    global current_b
    global current_epoch
    global loss_history


    # 현재 loss 저장
    y_pred = sigmoid(
        current_w * x
        +
        current_b
    )

    loss = calculate_loss(
        y,
        y_pred
    )

    loss_history.append(
        loss
    )


    # Learning Rate는 현재 슬라이더 값 사용
    lr = lr_slider.val


    # 경사하강법 1회
    current_w, current_b = (
        gradient_descent_step(
            current_w,
            current_b,
            lr
        )
    )


    current_epoch += 1


    update_graph()


# ============================================================
# 11. Gradient Descent 20회 실행
# ============================================================

def twenty_steps(event):

    for _ in range(20):

        one_step(None)


# ============================================================
# 12. Reset
# ============================================================

def reset(event):

    global current_w
    global current_b
    global current_epoch
    global loss_history

    current_w = weight_slider.val
    current_b = bias_slider.val

    current_epoch = 0

    loss_history = []

    update_graph()


# ============================================================
# 13. 버튼 생성
# ============================================================

step_axis = plt.axes([
    0.15,
    0.025,
    0.15,
    0.05
])

step_button = Button(
    step_axis,
    "1 Step"
)

step_button.on_clicked(
    one_step
)


steps_axis = plt.axes([
    0.35,
    0.025,
    0.15,
    0.05
])

steps_button = Button(
    steps_axis,
    "20 Steps"
)

steps_button.on_clicked(
    twenty_steps
)


reset_axis = plt.axes([
    0.55,
    0.025,
    0.15,
    0.05
])

reset_button = Button(
    reset_axis,
    "Reset"
)

reset_button.on_clicked(
    reset
)


# ============================================================
# 14. 처음 화면 표시
# ============================================================

update_graph()

plt.show()