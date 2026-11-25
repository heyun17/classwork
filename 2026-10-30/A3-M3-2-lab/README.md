# A3-M3-2 Chroma 실전 — 쇼핑몰 FAQ

## 설치
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   /   macOS·Linux: source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu   # GPU가 없으면 CPU판 먼저
pip install -r requirements.txt
```

## 파일
| 파일 | 내용 |
|---|---|
| shop_faq.csv | FAQ 20건 (faq_id, category, question, answer) |
| shop_faq_tests.csv | 평가 질문 12개 (question, gold_faq_id) |
| emb.py | 임베딩 함수 embed()와 모델 이름 (A3-M2-2와 같음) |
| 01_Chroma_저장과_검색.ipynb | 컬렉션 만들기, add·get·query (chroma_db/ 생성) |
| 02_메타데이터_필터와_수정.ipynb | where, where_document, update·upsert·delete |
| 03_RAG평가와_리랭킹.ipynb | Hit@1·MRR 평가, 리랭킹 |
| 04_실습과제.ipynb | 과제 3개 |

노트북은 01 → 02 → 03 → 04 순서로 실행합니다. 처음부터 다시 하려면 chroma_db 폴더를 지웁니다.
처음 실행할 때 모델 두 개(각 약 470MB)를 내려받습니다.
