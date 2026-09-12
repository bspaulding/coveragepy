"""Benchmark workload for coverage.py tracer overhead measurement.

Mix of:
  - tight single-line loops (repeats same line many times) -> line-event heavy
  - many small function calls (recursion) -> call/return-event heavy
  - branchy code -> exercises branch coverage arc recording
"""

def loop_sum(n):
    total = 0
    for i in range(n):
        total += i * 2 - 1
    return total


def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def collatz_len(n):
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps


def is_prime(n):
    if n < 2:
        return False
    for d in range(2, int(n ** 0.5) + 1):
        if n % d == 0:
            return False
    return True


def primes_below(n):
    return [x for x in range(2, n) if is_prime(x)]


def run():
    a = loop_sum(400_000)
    b = fib(23)
    c = sum(collatz_len(n) for n in range(1, 6000))
    d = len(primes_below(20_000))
    return (a, b, c, d)


if __name__ == "__main__":
    print(run())
