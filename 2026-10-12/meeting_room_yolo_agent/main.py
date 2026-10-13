from agent import run_agent


def main() -> None:
    print("=== 회의실 YOLO Agent ===")

    request = input("요청: ").strip()

    if not request:
        request = (
            "현재 회의실 이미지를 모두 분석하고 "
            "사람 수와 상태를 알려줘. "
            "마지막에는 공간 활용 방안도 간단히 제안해줘."
        )

    answer = run_agent(request)

    print()
    print("=== Agent 결과 ===")
    print(answer)


if __name__ == "__main__":
    main()
