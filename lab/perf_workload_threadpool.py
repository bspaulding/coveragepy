"""asyncio + ThreadPoolExecutor workload: exercises real OS threads spawned
via loop.run_in_executor, to check whether sysmon (sys.monitoring, which
registers globally rather than per-thread via threading.settrace) measures
code running on those worker threads correctly -- with and without the
concurrency=thread config that ctrace/pytrace require for this."""
import asyncio
from concurrent.futures import ThreadPoolExecutor


def blocking_work(n):
    total = 0
    for i in range(n):
        if i % 2 == 0:
            total += i
        else:
            total -= i
    return total


async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = await asyncio.gather(
            *(loop.run_in_executor(pool, blocking_work, 5000) for _ in range(16))
        )
    return sum(results)


def run():
    return asyncio.run(main())


if __name__ == "__main__":
    print(run())
