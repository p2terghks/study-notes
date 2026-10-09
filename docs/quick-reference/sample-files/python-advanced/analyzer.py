import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


class InvalidRow(ValueError):
    """CSV 형식 또는 행의 값이 잘못되었습니다."""


@dataclass(frozen=True)
class Student:
    name: str
    team: str
    score: int

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("이름은 비어 있지 않은 문자열이어야 합니다")
        if not isinstance(self.team, str) or not self.team.strip():
            raise ValueError("팀은 비어 있지 않은 문자열이어야 합니다")
        if type(self.score) is not int or not 0 <= self.score <= 100:
            raise ValueError("점수는 0~100 정수여야 합니다")

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        if self.score >= 80:
            return "B"
        if self.score >= 60:
            return "C"
        return "F"


def read_students(source: TextIO) -> Iterator[Student]:
    reader = csv.DictReader(source, strict=True)
    try:
        if reader.fieldnames != ["name", "team", "score"]:
            raise InvalidRow("헤더는 name,team,score 순서여야 합니다")
        for row in reader:
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("컬럼 개수가 다릅니다")
                yield Student(
                    name=row["name"].strip(),
                    team=row["team"].strip(),
                    score=int(row["score"]),
                )
            except (TypeError, ValueError) as exc:
                raise InvalidRow(f"{reader.line_num}행: {exc}") from exc
    except csv.Error as exc:
        raise InvalidRow(f"{reader.line_num}행: CSV 형식 오류: {exc}") from exc


def summarize(students: Iterable[Student]) -> dict[str, object]:
    count = 0
    total = 0
    grades: Counter[str] = Counter()
    teams: defaultdict[str, int] = defaultdict(int)
    passed: list[str] = []
    for student in students:
        count += 1
        total += student.score
        grades[student.grade] += 1
        teams[student.team] += 1
        if student.score >= 60:
            passed.append(student.name)
    return {
        "count": count,
        "average": round(total / count, 2) if count else None,
        "grades": dict(sorted(grades.items())),
        "teams": dict(sorted(teams.items())),
        "passed": passed,
    }


def analyze_file(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return summarize(read_students(source))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CSV 성적 분석기")
    parser.add_argument("input", type=Path, help="입력 CSV 경로")
    parser.add_argument("--output", type=Path, default=Path("report.json"))
    args = parser.parse_args(argv)
    try:
        report = analyze_file(args.input)
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        args.output.write_text(text, encoding="utf-8")
    except (OSError, UnicodeError, InvalidRow) as exc:
        parser.exit(2, f"오류: {exc}\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
