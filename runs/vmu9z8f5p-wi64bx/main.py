import asyncio
import time
import sys
from typing import (
    AsyncIterable, 
    TypeVar, 
    Generic, 
    Callable, 
    Iterable
)

T = TypeVar("T")
U = TypeVar("U")

class Stream(Generic[T]):
    def __init__(self, iterable: AsyncIterable[T]):
        self._iterable = iterable

    def __aiter__(self) -> AsyncIterable[T]:
        return self._iterable.__aiter__()

    @classmethod
    def from_iterable(cls, iterable: Iterable[T]) -> 'Stream[T]':
        async def _gen():
            for item in iterable:
                yield item
        return cls(_gen())

    def map(self, func: Callable[[T], U]) -> 'Stream[U]':
        async def _gen():
            async for item in self._iterable:
                yield func(item)
        return Stream(_gen())

    def filter(self, predicate: Callable[[T], bool]) -> 'Stream[T]':
        async def _gen():
            async for item in self._iterable:
                if predicate(item):
                    yield item
        return Stream(_gen())

    async def reduce(self, func: Callable[[U, T], U], initial: U) -> U:
        accumulator = initial
        async for item in self._iterable:
            accumulator = func(accumulator, item)
        return accumulator

    async def collect(self) -> list[T]:
        return [item async for item in self._iterable]

async def run_benchmark():
    N = 1_000_000
    async def producer():
        for i in range(N):
            yield i

    start_time = time.perf_counter()
    stream = Stream(producer())
    result = await (
        stream.filter(lambda x: x % 2 == 0)
              .map(lambda x: x * x)
              .reduce(lambda acc, x: acc + x, 0)
    )
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    n = 499_999
    expected = 4 * (n * (n + 1) * (2 * n + 1) // 6)

    print(f"Resultado: {result}")
    print(f"Esperado: {expected}")
    print(f"Tempo: {duration:.4f}s")
    
    assert duration < 5, f"Tempo muito alto: {duration}s"
    assert result == expected, "Erro no cálculo"
    print("Benchmark APROVADO")

async def test_types():
    async def gen():
        yield 1
    s: Stream[int] = Stream(gen())
    s_str: Stream[str] = s.map(lambda x: str(x))
    res = await s_str.collect()
    assert res == ["1"]
    print("Tipagem lógica validada")

if __name__ == "__main__":
    asyncio.run(test_types())
    asyncio.run(run_benchmark())