"""Asyncio workload to check sys.monitoring (sysmon) compatibility with coroutines."""
import asyncio


async def worker(n):
    total = 0
    for i in range(n):
        if i % 2 == 0:
            total += i
        else:
            total -= i
        if i % 1000 == 0:
            await asyncio.sleep(0)
    return total


async def main():
    results = await asyncio.gather(*(worker(3000) for _ in range(20)))
    return sum(results)


def run():
    return asyncio.run(main())


if __name__ == "__main__":
    print(run())
