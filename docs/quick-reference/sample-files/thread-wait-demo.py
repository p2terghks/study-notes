"""순차 실행과 스레드의 대기 중첩 비교. CPU 성능 벤치마크가 아닙니다."""
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor


def wait_task(number):
    time.sleep(0.2)  # 외부 I/O 없이 대기만 흉내 냅니다.
    return number, os.getpid(), threading.get_ident()


def report(label, start, results):
    print(f"\n{label}: {time.perf_counter() - start:.3f}초")
    for number, pid, thread_id in results:
        print(f"작업 {number}: PID={pid}, 스레드 ID={thread_id}")
    assert [item[0] for item in results] == list(range(4))
    assert all(item[1] == os.getpid() for item in results)


if __name__ == "__main__":
    start = time.perf_counter()
    report("순차 대기", start, [wait_task(i) for i in range(4)])
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(wait_task, range(4)))
    report("4개 스레드로 대기 겹치기", start, results)
    print("\nsleep 대기가 겹친 결과이며 CPU 계산의 병렬 성능을 뜻하지 않습니다.")
