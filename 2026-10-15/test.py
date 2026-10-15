import cv2

img = cv2.imread("receipt.jpg", 0)

# 약간의 노이즈 제거
img = cv2.GaussianBlur(img, (3, 3), 0)

# 적응형 이진화
binary = cv2.adaptiveThreshold(
    img,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    31,
    10
)

cv2.imshow("original", img)
cv2.imshow("binary", binary)
cv2.waitKey(0)
cv2.destroyAllWindows()