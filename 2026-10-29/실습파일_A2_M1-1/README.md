# A2-M1 Transformer 3 Part 개정 실습

Python 3.10+ 표준 라이브러리만 사용합니다. Windows PowerShell에서 이 폴더로 이동한 다음 실행하세요.

```powershell
python 01_token_ids.py
python 02_padding_mask.py
python 03_embedding.py
python 04_position.py
python 05_qkv_attention.py
python 06_causal_mask.py
python 07_ffn_norm.py
python 08_lm_head.py
python 09_a1_bridge_demo.py
python -m unittest discover -s tests -v
```

`toy_core.py`는 01~08 실습의 공통 함수를 제공합니다. 교안은 함수 내부 원리를 설명한 다음 import 합니다. `09_a1_bridge_demo.py`는 실제 A1 CSV가 없이도 실행되는 모형이며, 원본 판정 코드나 실제 규칙 스키마를 대체하지 않습니다. 모든 숫자는 고정된 교육용 값입니다.

전체 교안 HTML은 ZIP 바깥 파일로 별도 제공됩니다. © 2026 부성순.
