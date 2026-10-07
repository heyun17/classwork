# Shop

FastAPI와 MySQL 기반 상품 목록 예제입니다. 설정값은 환경 변수에서 읽고, DB 접근·업무 로직·HTTP 라우트를 분리했습니다.

## 실행

1. 의존성을 설치합니다.

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. `.env.example`을 참고해 `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` 환경 변수를 설정합니다.

3. 개발 서버를 실행합니다.

   ```powershell
   uvicorn main:app --reload
   ```

4. 브라우저에서 `http://127.0.0.1:8000/`을 엽니다.

## 검증

DB 없이 서비스 계층 단위 테스트를 실행할 수 있습니다.

```powershell
python -m unittest discover -s . -p "test_product_service.py"
```

DB 연결을 별도로 확인하려면 다음을 실행합니다.

```powershell
python test.py
```

자세한 동작과 오류 기준은 [기능명세서.md](기능명세서.md)를 참고합니다.
