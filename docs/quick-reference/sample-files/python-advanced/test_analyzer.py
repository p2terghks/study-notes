import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from analyzer import InvalidRow, Student, analyze_file, main, read_students, summarize


class AnalyzerTests(unittest.TestCase):
    def test_report(self):
        source = StringIO("name,team,score\nKim,A,90\nLee,A,80\nPark,B,50\n")
        self.assertEqual(summarize(read_students(source)), {
            "count": 3, "average": 73.33,
            "grades": {"A": 1, "B": 1, "F": 1},
            "teams": {"A": 2, "B": 1}, "passed": ["Kim", "Lee"],
        })

    def test_empty_rows(self):
        report = summarize(read_students(StringIO("name,team,score\n")))
        self.assertEqual(report, {
            "count": 0, "average": None, "grades": {}, "teams": {}, "passed": [],
        })

    def test_grade_boundaries(self):
        for score, grade in [(0, "F"), (59, "F"), (60, "C"), (79, "C"),
                             (80, "B"), (89, "B"), (90, "A"), (100, "A")]:
            with self.subTest(score=score):
                self.assertEqual(Student("Kim", "A", score).grade, grade)

    def test_invalid_model(self):
        for name, team, score in [("", "A", 90), ("Kim", " ", 90),
                                  ("Kim", "A", -1), ("Kim", "A", 101),
                                  ("Kim", "A", True), ("Kim", "A", 90.0)]:
            with self.subTest(name=name, team=team, score=score):
                with self.assertRaises(ValueError):
                    Student(name, team, score)

    def test_invalid_rows_include_line(self):
        for row in ["Kim,A,abc", "Kim,A,101", "Kim,A", "Kim,A,90,extra", ",A,90"]:
            with self.subTest(row=row):
                with self.assertRaisesRegex(InvalidRow, "2행"):
                    list(read_students(StringIO("name,team,score\n" + row + "\n")))

    def test_invalid_header(self):
        for content in ["", "name,score,team\n", "name,team,score,extra\n"]:
            with self.subTest(content=content):
                with self.assertRaisesRegex(InvalidRow, "헤더"):
                    list(read_students(StringIO(content)))

    def test_quoted_name(self):
        source = StringIO('name,team,score\n"Kim, Jr",A,90\n')
        self.assertEqual(summarize(read_students(source))["passed"], ["Kim, Jr"])

    def test_csv_format_error(self):
        with self.assertRaisesRegex(InvalidRow, "CSV 형식 오류"):
            list(read_students(StringIO('name,team,score\n"Kim,A,90\n')))

    def test_cli_output_and_bom(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "students.csv"
            output = Path(directory) / "report.json"
            source.write_text("name,team,score\nKim,A,90\n", encoding="utf-8-sig")
            with redirect_stdout(StringIO()):
                self.assertEqual(main([str(source), "--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                             analyze_file(source))

    def test_invalid_input_preserves_existing_output(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "students.csv"
            output = Path(directory) / "report.json"
            source.write_text("name,team,score\nKim,A,999\n", encoding="utf-8")
            output.write_text("previous report", encoding="utf-8")
            with self.assertRaises(SystemExit) as error:
                main([str(source), "--output", str(output)])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous report")


if __name__ == "__main__":
    unittest.main()
