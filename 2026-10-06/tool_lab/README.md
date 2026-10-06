# 파이썬 구조 잡기 · Part 1 실습 파일

제공되는 것은 `sales.csv` 하나입니다. 나머지는 교안을 보고 직접 만듭니다.

```
tool_lab/
├── sales.csv            제공
├── main.py              4장에서 작성
└── tools/
    ├── __init__.py      4장
    ├── loader.py        1장
    ├── registry.py      2 · 3장
    ├── sales_tools.py   1 · 3장
    └── autoload.py      4장
```

## 완성 후 실행

```bash
python3 main.py list
python3 main.py schema summarize_sales
python3 main.py call summarize_sales '{"top_n":2}'
python3 main.py call region_detail '{"region":"서울","min_amount":1000000}'
```

모든 명령은 `tool_lab` 폴더에서 실행합니다.
