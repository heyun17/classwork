# dbload.py 작업 설명서

## 1. 목적

Python에서 .db 파일을 SQLite 데이터베이스로 읽는 방법을 익히고, CSV와
비교할 수 있는 기본 집계를 수행한다.

dbload.py는 다음 항목을 출력한다.

- 전체 레코드 건수
- region별 건수와 전체 대비 비율
- qty의 합계와 평균
- date의 년월(YYYY-MM)별 amount 합계
- 전체 처리 시간

## 2. 현재 데이터 구성

이번 실습에서는 큰 1,000,000건 파일 대신 sales_100k.csv를 사용했다.

- 원본 CSV: data/sales_100k.csv
- 실행 대상 DB: data/sales_100k.db
- DB 안의 테이블: sales
- 레코드 수: 100,000건

실행 대상 파일 이름은 원래 지시된 sales_100k.db를 그대로 유지했다. 다만
그 안에 들어 있는 데이터는 sales_100k.csv에서 import한 100,000건이다.
sales_1m.csv와 sales_100k.csv 원본은 변경하지 않았다.

## 3. 실행 방법

PowerShell에서 다음 명령을 실행한다.

~~~powershell
Set-Location 'D:\OneDrive\#classes\September\0915\classwork\csv-lab'
python .\dbload.py
~~~

프로그램은 dbload.py의 위치를 기준으로 data/sales_100k.db를 찾으므로,
현재 폴더가 달라도 파일의 전체 경로로 실행하면 정상적으로 동작한다.

## 4. SQLite DB로 만든 과정

처음의 sales_100k.db는 CSV 파일의 확장자만 .db로 바꾼 파일이었다.
확장자는 파일 형식을 바꾸지 않으므로 sqlite3로 열 때 file is not a
database 오류가 발생한다.

이를 해결하기 위해 sales_100k.csv를 읽어 실제 SQLite DB를 새로 만들었다.

~~~sql
CREATE TABLE sales (
    date TEXT NOT NULL,
    region TEXT,
    product TEXT,
    amount INTEGER,
    qty INTEGER,
    memo TEXT
);
~~~

CSV의 100,000개 행을 위 테이블에 넣은 뒤 region과 date에 인덱스를 만들고,
DB의 행 수가 100,000건인지 확인했다. 따라서 현재 sales_100k.db는 실제
SQLite 파일이며 Python의 sqlite3.connect()로 읽을 수 있다.

## 5. 코드 설명

### DB 연결

프로그램은 SQLite 파일의 첫 16바이트를 검사한다. SQLite format 3으로
시작하지 않으면 잘못된 파일이라는 오류를 출력한다.

연결 후 PRAGMA query_only = ON을 사용한다. 이 프로그램은 조회와 집계만
수행하므로 원본 DB가 수정되지 않는다. Windows 경로의 특수문자 문제를 피하기
위해 일반 파일 경로로 연결한다.

### 전체 건수

SELECT COUNT(*) FROM sales로 테이블의 전체 행 수를 확인한다.
COUNT(*)는 컬럼 값이 NULL이어도 행을 세기 때문에 전체 건수를 구할 때
사용한다.

### region별 건수와 비율

GROUP BY region으로 지역별로 묶은 뒤 COUNT(*)로 건수를 센다.
비율은 다음 식으로 계산한다.

~~~text
지역별 비율(%) = 지역별 건수 / 전체 건수 * 100
~~~

### qty 합계와 평균

SUM(qty)와 AVG(qty)를 사용한다.

~~~sql
SELECT SUM(qty), AVG(qty)
FROM sales;
~~~

### 년월별 판매금액

날짜가 YYYY-MM-DD 형식이므로 substr(date, 1, 7)로 YYYY-MM만
추출한다. 이후 월별로 그룹화하고 SUM(amount)를 계산한다.

~~~sql
SELECT substr(date, 1, 7), SUM(amount)
FROM sales
GROUP BY substr(date, 1, 7)
ORDER BY substr(date, 1, 7);
~~~

## 6. CSV와 속도 비교

dbload.py 마지막에 표시되는 처리 시간은 DB 연결과 SQL 집계에 걸린 시간이다.
속도 비교를 정확히 하려면 CSV에서도 같은 네 가지 집계를 수행하고, 두
프로그램을 여러 번 실행해 평균을 비교해야 한다.

SQLite는 자료가 테이블과 숫자 자료형으로 준비되어 있고 인덱스를 사용할
수 있다. CSV는 매번 텍스트를 읽고 문자열을 숫자로 변환해야 한다. 다만
운영체제 파일 캐시, 디스크 속도, Python 버전 등에 따라 결과가 달라질 수
있으므로 한 번의 측정만으로 결론을 내리지 않는 것이 좋다.
