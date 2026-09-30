import sys

data = list(map(int, sys.stdin.buffer.read().split()))
it = iter(data)
n, q = next(it), next(it)
prefix = [0] * (n + 1)
for i in range(1, n + 1):
    prefix[i] = prefix[i - 1] + next(it)
answers = []
for _ in range(q):
    left, right = next(it), next(it)
    answers.append(str(prefix[right] - prefix[left - 1]))
sys.stdout.write("\n".join(answers))
