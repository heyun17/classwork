# MediaPipe 얼굴 랜드마크 번호 출력

이 프로젝트는 얼굴 사진을 MediaPipe로 분석하여 얼굴 위에
**랜드마크 점, Mesh 연결선, 랜드마크 번호**를 표시하는 Python 예제이다.

최종 결과물은 다음 파일이다.

```text
face_landmarks.jpg
```

---

# 1. 전체 작업 흐름

```text
1. Python 확인
      ↓
2. 필요한 라이브러리 설치
      ↓
3. 프로젝트 폴더 준비
      ↓
4. face.jpg 넣기
      ↓
5. face_landmark_index.py 실행
      ↓
6. MediaPipe가 얼굴 검출
      ↓
7. 얼굴 Landmark 추출
      ↓
8. 점 + 번호 + Mesh 선 표시
      ↓
9. face_landmarks.jpg 저장
      ↓
10. 결과 확인
```

---

# 2. 프로젝트 폴더

예:

```text
face_project/
├─ 작업지시서.md
├─ README.md
├─ face_landmark_index.py
└─ face.jpg
```

프로그램 실행 후:

```text
face_project/
├─ 작업지시서.md
├─ README.md
├─ face_landmark_index.py
├─ face.jpg
└─ face_landmarks.jpg
```

---

# 3. 필요한 프로그램

- Windows 10 또는 Windows 11
- Python 3
- MediaPipe
- OpenCV

---

# 4. Python 설치 확인

CMD 또는 PowerShell을 연다.

```powershell
py --version
```

예:

```text
Python 3.12.4
```

버전이 나오면 Python이 설치된 것이다.

`py`가 동작하지 않는 경우:

```powershell
python --version
```

을 확인한다.

---

# 5. 라이브러리 설치

처음 한 번만 실행한다.

```powershell
py -m pip install mediapipe opencv-python
```

이미 설치되어 있는지 먼저 확인하려면:

```powershell
py -c "import cv2, mediapipe; print('OK')"
```

다음처럼 나오면 설치되어 있다.

```text
OK
```

---

# 6. 얼굴 이미지 준비

분석할 얼굴 사진의 이름을 다음과 같이 맞춘다.

```text
face.jpg
```

그리고 `face_landmark_index.py`와 같은 폴더에 둔다.

```text
face_project/
├─ face_landmark_index.py
└─ face.jpg
```

권장 이미지:

- 얼굴이 정면에 가까운 사진
- 얼굴 전체가 보이는 사진
- 너무 어둡지 않은 사진
- 얼굴이 지나치게 작지 않은 사진
- 가능하면 한 명만 있는 사진

---

# 7. 프로그램 실행

PowerShell 또는 CMD에서 프로젝트 폴더로 이동한다.

예:

```powershell
cd C:\face_project
```

실행:

```powershell
py face_landmark_index.py
```

`py`가 없는 환경에서는:

```powershell
python face_landmark_index.py
```

---

# 8. 프로그램 내부 처리 순서

프로그램은 다음 순서로 처리한다.

## Step 1. 이미지 읽기

```text
face.jpg
```

파일을 OpenCV가 읽는다.

## Step 2. 이미지 크기 확인

사진이 너무 작으면 랜드마크 번호가 잘 보이도록 확대할 수 있다.

## Step 3. MediaPipe 실행

MediaPipe가 얼굴을 찾는다.

## Step 4. 얼굴 랜드마크 추출

기본 설정에서는 얼굴의 468개 랜드마크를 사용한다.

```text
0
1
2
3
...
467
```

## Step 5. Mesh 연결선 표시

얼굴의 각 랜드마크를 연결하여 Face Mesh를 그린다.

## Step 6. 번호 표시

각 점 옆에 해당 랜드마크 인덱스를 표시한다.

예:

```text
33
133
362
263
...
```

## Step 7. 결과 저장

최종 결과를 저장한다.

```text
face_landmarks.jpg
```

---

# 9. 정상 실행 예

콘솔:

```text
랜드마크 개수: 468
결과 저장 완료: C:\face_project\face_landmarks.jpg
아무 키나 누르면 종료됩니다.
```

그리고 결과 이미지 창이 열린다.

이미지에는 대략 다음이 표시된다.

```text
얼굴
├─ Landmark 점
├─ Landmark 번호
└─ Face Mesh 연결선
```

---

# 10. 결과 파일 확인

프로젝트 폴더에 다음 파일이 생겼는지 확인한다.

```text
face_landmarks.jpg
```

정상 결과:

- 얼굴 위에 많은 작은 점이 있음
- 각 점 주변에 숫자가 있음
- 얼굴 전체에 Mesh 선이 연결되어 있음

---

# 11. 자주 발생하는 오류

## Python을 찾을 수 없음

예:

```text
'py' is not recognized
```

다음 명령을 확인한다.

```powershell
python --version
```

Python 자체가 없다면 Python을 먼저 설치해야 한다.

---

## MediaPipe가 없음

예:

```text
ModuleNotFoundError: No module named 'mediapipe'
```

설치:

```powershell
py -m pip install mediapipe
```

---

## OpenCV가 없음

예:

```text
ModuleNotFoundError: No module named 'cv2'
```

설치:

```powershell
py -m pip install opencv-python
```

---

## face.jpg를 찾을 수 없음

예:

```text
이미지를 찾을 수 없습니다: face.jpg
```

폴더가 다음과 같은지 확인한다.

```text
face_project/
├─ face_landmark_index.py
└─ face.jpg
```

주의:

```text
face.jpg.jpg
Face.jpg
face.jpeg
```

등은 파일명이 다르다.

Windows에서 확장자가 숨겨져 있으면 실제 파일명을 확인한다.

---

## 얼굴을 찾지 못함

예:

```text
얼굴을 찾지 못했습니다.
```

다른 정면 얼굴 사진으로 먼저 테스트한다.

가능한 원인:

- 얼굴이 너무 작음
- 얼굴이 옆을 보고 있음
- 사진이 너무 어두움
- 얼굴 일부가 잘림
- 이미지가 손상됨

---

# 12. Codex에게 작업시키는 방법

프로젝트 폴더를 Codex가 작업할 수 있는 위치에 둔다.

먼저 Codex에게 다음과 같이 지시한다.

```text
작업지시서.md를 먼저 읽고 지시된 작업을 수행해줘.
README.md는 전체 작업 순서를 참고해.
```

중요:

```text
작업지시서.md
```

에는 오류 처리, 수정 범위, 토큰 효율화, 완료 조건이 들어 있으므로
Codex는 이 문서를 우선 기준으로 작업한다.

---

# 13. Codex 권장 작업 순서

```text
작업지시서.md 읽기
        ↓
README.md 확인
        ↓
프로젝트 파일 목록 확인
        ↓
face_landmark_index.py 확인
        ↓
face.jpg 존재 확인
        ↓
Python / 라이브러리 확인
        ↓
프로그램 실행
        ↓
오류 발생?
   ┌────┴────┐
  YES       NO
   │         │
오류 원인    결과 파일 확인
최소 수정       │
   │            ↓
재실행       완료 보고
   │
   └──── 반복
```

---

# 14. 작업 시 중요한 원칙

Codex는 다음 방식으로 작업한다.

### 정상 코드 보존

이미 정상인 코드는 건드리지 않는다.

### 최소 수정

오류 발생 부분만 수정한다.

### 반복 읽기 최소화

같은 파일 전체를 계속 다시 읽지 않는다.

### 불필요한 설치 금지

이미 설치된 라이브러리를 반복 설치하지 않는다.

### 작업 범위 유지

현재 프로젝트의 목표는 다음까지이다.

```text
얼굴 → Landmark 검출 → 번호 표시 → 결과 이미지 생성
```

얼굴 비대칭 계산이나 클라우드 연결은 다음 단계이다.

---

# 15. 완료 기준

아래 조건을 모두 만족하면 성공이다.

- [ ] Python 코드가 실행된다.
- [ ] MediaPipe가 얼굴을 검출한다.
- [ ] 얼굴 Landmark를 추출한다.
- [ ] Landmark 번호가 이미지에 표시된다.
- [ ] Mesh 연결선이 표시된다.
- [ ] `face_landmarks.jpg`가 생성된다.

---

# 16. 다음 단계

현재 단계:

```text
얼굴 Landmark 시각화
```

이 작업이 완료된 후 다음 단계에서 구현할 수 있다.

```text
Landmark
   ↓
얼굴 기울기 보정
   ↓
얼굴 중앙선 계산
   ↓
좌우 대응점 선택
   ↓
거리 / 각도 비교
   ↓
비대칭 수치 계산
   ↓
얼굴 비대칭 점수
```

이 단계는 현재 작업과 분리해서 진행한다.
