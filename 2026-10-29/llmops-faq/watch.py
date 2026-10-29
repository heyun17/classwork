"""터미널에서 켜 두면 data/ 폴더를 지켜보다가 바뀌는 순간 파이프라인을 자동으로 실행한다.
실행:  python watch.py        (멈추기: Ctrl+C)
실제 서비스의 'S3 업로드 이벤트·Git push·스케줄러' 역할을 5초 간격 확인으로 대신한다."""
import time
from llmops_core import init_project, check_and_run, status

INTERVAL = 5  # 초

if __name__ == "__main__":
    init_project()
    print(f"data/ 폴더를 {INTERVAL}초마다 확인합니다. faq.csv · synonyms.csv · eval_set.jsonl을 고쳐 보세요. (멈추기: Ctrl+C)\n")
    try:
        while True:
            if check_and_run(quiet=True):
                status()
                print()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n감시를 멈춥니다.")
