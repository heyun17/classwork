# STEP 2. pdfplumber가 표를 어떻게 봤는지 그림으로 확인
import pdfplumber

PDF_PATH = "표샘플_어려움.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[0]
    image = page.to_image(resolution=110)                 # 쪽을 그림으로 (PageImage)
    image.debug_tablefinder()                             # 찾은 선(빨강)·교차점·칸(파랑)을 겹쳐 그림
    image.save("debug_easy.png")
    print("debug_easy.png 저장")
