import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("카메라를 열 수 없습니다")

try:
    while True:
        ok, frame = cap.read()

        if not ok:
            break

        cv2.imshow("webcam", frame)

        # q 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # 창의 X 버튼으로 닫아도 종료
        if cv2.getWindowProperty("webcam", cv2.WND_PROP_VISIBLE) < 1:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()