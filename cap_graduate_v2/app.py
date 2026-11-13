from pathlib import Path
import re
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from rules import CREDITS, TARGET, catalog, key, report

# OCR 과목명을 교육과정 목록과 비교하는 match를 complete_name으로 호출한다.
from matcher import match as complete_name


# OCR 한 행의 과목명을 보정하고 학점·영역을 조회해 검토용 문자열로 반환
def review_row(line, track):
    # 사전에서 과목명을 조회하며, 해당 키가 없으면 None을 받음
    name = line.get("과목명")
    # 과목명 셀이 따로 없으면 OCR이 읽은 전체 행에서 이름을 추출
    if name is None:
        text = line["text"].strip()
        # 열 제목이 들어 있는 행은 수강 과목이 아니므로 제외
        if "과목명" in text and "학점" in text:
            return None
        # 표를 구분하지 못한 경우 행에서 학점·성적·과목번호를 제거해 과목명 추출
        name = re.sub(
            r"\s+\d+\s+(?:[A-DF][0+-]?|P(?:ASS)?)(?:\s.*)?$", "", text, flags=re.I
        )
        name = re.sub(r"^.*?\b(?:[A-Z]+\d+|\d{5,})\s+", "", name)
    name = complete_name(name, track)
    # 표준화한 과목명을 키로 학점을 조회하며, 미등록 과목은 None
    credit = CREDITS.get(key(name))
    # 조회 결과의 첫 값(이름)은 _에 받고, 사용할 두 번째 값(영역)은 category에 저장
    _, category = catalog(track).get(
        key(name), (name, "0학점" if credit == 0 else "확인 필요")
    )
    # 학점은 문자열로 바꾸고 세 항목을 |로 연결해 검토표 한 줄을 생성
    return " | ".join([name, "" if credit is None else str(credit), category])


# 졸업요건 확인 앱의 화면을 구성하고 사용자 입력을 처리
def main():
    root = tk.Tk()
    # 앱 창의 제목을 지정
    root.title("cap_graduate v2 · 졸업요건 확인")
    # 앱 창의 초기 크기를 가로 900·세로 700으로 지정
    root.geometry("900x700")
    bar = ttk.Frame(root, padding=10)
    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    bar.pack(fill="x")

    # 제목과 선택지 목록을 받아 입학년도·전공 선택 상자를 생성
    def choice(label, values):
        # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
        ttk.Label(bar, text=label).pack(side="left")
        box = ttk.Combobox(bar, values=values, state="readonly", width=8)
        # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
        box.pack(side="left", padx=5)
        # 선택지의 0번 항목을 기본값으로 선택
        box.current(0)
        return box

    choice("입학년도", ["2022"])
    track = choice("전공", ["정보", "멀콘", "인공"])
    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    ttk.Label(
        root,
        text="이수 완료한 과목만 남겨 주세요. F·수강 중 과목은 삭제하세요. 행 형식: 과목명 | 학점 | 영역",
    ).pack(anchor="w", padx=10)
    editor = ScrolledText(root, height=11, wrap="none", undo=True)
    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    editor.pack(fill="both", expand=True, padx=10)
    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    ttk.Label(
        root, text="직접 입력할 수 있는 영역: " + ", ".join(TARGET), wraplength=810
    ).pack(anchor="w", padx=10)
    events = queue.Queue()

    # 여러 성적표 사진을 선택받고 OCR 작업을 시작
    def load():
        # 여러 사진을 선택할 수 있는 창을 열고 선택한 파일 경로들을 반환
        files = filedialog.askopenfilenames(
            filetypes=[("성적표 사진", "*.png *.jpg *.jpeg *.webp"), ("모든 파일", "*")]
        )
        # 사진 선택을 취소했으면 OCR 작업을 시작하지 않고 종료
        if not files:
            return
        # 전공 선택 상자에 현재 선택된 문자열을 읽음
        selected = track.get()
        # OCR 처리 중 중복 요청을 막기 위해 사진 선택 버튼 비활성화
        button.configure(state="disabled")
        # 진행 상태 문자열을 바꾸면 연결된 화면 문구도 갱신
        status.set("사진 읽는 중…")

        # 선택한 사진을 한 장씩 인식하고 검토 결과를 화면 전달 큐에 저장
        def worker():
            try:
                # 이미지를 ocr 입력으로
                from ocr import recognize

                for path in files:
                    # 사진 파일을 바이트로 읽어 recognize에 전달하고 OCR 행 목록을 받음
                    lines, _ = recognize(Path(path).read_bytes())
                    # 인식된 행이 하나도 없으면 파일명을 포함한 오류를 표시
                    if not lines:
                        raise ValueError("글자를 찾지 못했어요: " + Path(path).name)
                    # 화면을 직접 수정하지 않고 결과·오류·완료 신호를 큐로 전달
                    events.put(
                        (
                            "rows",
                            [
                                row
                                for line in lines
                                if (row := review_row(line, selected))
                            ],
                        )
                    )
            # 발생한 오류를 exc에 받아 사용자에게 원인을 전달
            except Exception as exc:
                # 화면을 직접 수정하지 않고 결과·오류·완료 신호를 큐로 전달
                events.put(("error", str(exc)))
            finally:
                # 화면을 직접 수정하지 않고 결과·오류·완료 신호를 큐로 전달
                events.put(("done", None))

        threading.Thread(target=worker, daemon=True).start()

    # 작업 큐의 결과를 확인해 검토표·오류 메시지·진행 상태를 갱신
    def poll():
        # 큐에 처리할 사건이 남아 있는 동안 하나씩 꺼내 화면에 반영
        while not events.empty():
            # 큐에서 처리할 사건 하나를 꺼내 종류와 데이터로 나눔
            kind, value = events.get()
            # 큐에서 받은 데이터가 과목 행이면 검토표에 추가
            if kind == "rows":
                # 여러 과목 행을 줄바꿈으로 연결해 검토표의 지정 위치에 삽입
                editor.insert("end", "\n".join(value) + "\n")
            # 큐에서 받은 데이터가 오류이면 오류 대화상자를 표시
            elif kind == "error":
                # OCR 작업의 오류 내용을 대화상자로 표시
                messagebox.showerror("사진 읽기", value)
            else:
                # 다른 사진을 선택할 수 있도록 버튼 활성화
                button.configure(state="normal")
                # 진행 상태 문자열을 바꾸면 연결된 화면 문구도 갱신
                status.set("과목별 내용을 확인하세요.")
        # 150밀리초 후 poll을 다시 호출해 작업 결과를 확인
        root.after(150, poll)

    button = ttk.Button(bar, text="사진 선택 (여러 장 가능)", command=load)
    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    button.pack(side="left", padx=12)
    status = tk.StringVar()
    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    ttk.Label(bar, textvariable=status).pack(side="left")

    # 검토한 과목 정보를 확인하고 졸업요건 비교 결과를 화면에 표시
    def calculate():
        try:
            # 검토표 전체 문자열을 읽고 줄별로 나눈 뒤 | 기준으로 세 항목을 분리
            rows = [
                [v.strip() for v in line.split("|")]
                for line in editor.get("1.0", "end").splitlines()
                if line.strip()
            ]
            # 입력이 없거나 과목명·학점·영역의 세 칸으로 나뉘지 않으면 계산 중단
            if not rows or any(len(row) != 3 for row in rows):
                raise ValueError("각 행을 과목명 | 학점 | 영역 형식으로 입력하세요.")
            changes = []
            filled = False

            for row in rows:
                # 전공 선택 상자에 현재 선택된 문자열을 읽음
                suggested = complete_name(row[0], track.get())
                # 보정한 이름이 입력 이름과 다르면 변경 목록에 기록하고 이름·영역 수정
                if suggested != row[0]:
                    changes.append(f"{row[0]} → {suggested}")
                    row[0] = suggested
                    # 전공 선택 상자에 현재 선택된 문자열을 읽음
                    row[2] = catalog(track.get()).get(
                        key(suggested), (suggested, row[2])
                    )[1]
                expected = CREDITS.get(key(row[0]))

                # 등록 학점은 있지만 입력값이 빈칸 또는 숫자가 아니면 목록의 학점으로 채움
                if expected is not None and not row[1].isdecimal():
                    row[1] = str(expected)
                    filled = True
                # 입력 학점이 목록의 학점과 다르면 변경 내용을 사용자에게 확인
                elif expected is not None and int(row[1]) != expected:
                    changes.append(f"{row[0]}: 입력 {row[1]}학점 → 목록 {expected}학점")
                    row[1] = str(expected)

            # 이름이나 학점의 변경 사항이 있을 때만 적용 여부를 질문
            if changes:
                # 사용자가 자동 변경 적용을 거절하면 이번 계산을 종료
                if not messagebox.askyesno(
                    "과목 정보 확인", "\n".join(changes) + "\n이대로 적용할까요?"
                ):
                    return
            # 빈 학점을 채웠거나 수정 사항이 있으면 검토표를 수정된 내용으로 다시 표시
            if filled or changes:
                # 검토표의 첫 줄 첫 글자(1.0)부터 끝(end)까지 기존 내용을 삭제
                editor.delete("1.0", "end")
                # 여러 과목 행을 줄바꿈으로 연결해 검토표의 지정 위치에 삽입
                editor.insert("1.0", "\n".join(" | ".join(row) for row in rows))
            # 전공 선택 상자에 현재 선택된 문자열을 읽음
            result = report(rows, track.get())
        # 발생한 오류를 exc에 받아 사용자에게 원인을 전달
        except ValueError as exc:
            # 입력값을 고쳐야 하는 이유를 안내 대화상자로 표시
            messagebox.showinfo("입력 확인", str(exc))
            return

        # 결과창에 내용을 쓸 수 있도록 잠시 편집 허용
        output.configure(state="normal")
        # 이전 계산 결과를 첫 글자부터 끝까지 비움
        output.delete("1.0", "end")
        # 새로 계산한 결과 문자열을 결과창 끝에 삽입
        output.insert("end", result)
        # 결과를 사용자가 직접 수정하지 못하도록 읽기 전용으로 전환
        output.configure(state="disabled")

    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    ttk.Button(root, text="확인한 내역으로 졸업요건 비교", command=calculate).pack(
        pady=8
    )
    output = ScrolledText(root, state="disabled", wrap="word")
    # 지정한 방향·여백·확장 옵션으로 위젯을 창에 배치
    output.pack(fill="both", expand=True, padx=10, pady=6)
    poll()
    # 창을 유지하며 버튼 클릭·입력 등의 이벤트를 처리
    root.mainloop()


# 이 파일을 직접 실행했을 때만 main을 시작하고 import할 때는 시작하지 않음
if __name__ == "__main__":
    main()
