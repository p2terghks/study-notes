"""세 점수를 입력받아 평균과 합격자 수를 출력합니다."""


def read_score(index):
    while True:
        try:
            score = int(input(f"Score {index}: "))
        except ValueError:
            print("Enter an integer from 0 to 100.")
            continue
        if 0 <= score <= 100:
            return score
        print("Enter an integer from 0 to 100.")


def main():
    scores = []
    try:
        for index in range(1, 4):
            scores.append(read_score(index))
    except EOFError:
        print("Input ended before all scores were entered.")
        return 1

    average = sum(scores) / len(scores)
    passed = sum(1 for score in scores if score >= 60)
    print(f"Average: {average:.2f}")
    print(f"Passed: {passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
