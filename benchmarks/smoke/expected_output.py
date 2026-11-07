"""Independent reference for collatz.c; prints the expected stdout line."""
import sys


def steps(n):
    s = 0
    while n != 1:
        n = 3 * n + 1 if n & 1 else n // 2
        s += 1
    return s


limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
total = best = best_steps = 0
best = 1
for i in range(1, limit + 1):
    s = steps(i)
    total += s
    if s > best_steps:
        best_steps, best = s, i
print(f"collatz limit={limit} total_steps={total} longest={best} steps={best_steps}")
