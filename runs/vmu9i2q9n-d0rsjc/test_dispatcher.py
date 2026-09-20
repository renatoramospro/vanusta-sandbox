import asyncio
import time
import pytest

class TaskDispatcher:
    def __init__(self, max_concurrency: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.active_count = 0
        self.max_observed_concurrency = 0
        self._lock = asyncio.Lock()

    async def _track_concurrency_enter(self):
        async with self._lock:
            self.active_count += 1
            if self.active_count > self.max_observed_concurrency:
                self.max_observed_concurrency = self.active_count

    async def _track_concurrency_exit(self):
        async with self._lock:
            self.active_count -= 1

    async def run_task(self, coro_func, timeout: float = None):
        """
        Executa uma corrotina respeitando o limite do semáforo e timeout granular.
        O timeout agora engloba inclusive o tempo de espera na fila do semáforo,
        evitando bloqueios indefinidos.
        """
        async def _wrapped():
            async with self.semaphore:
                await self._track_concurrency_enter()
                try:
                    return await coro_func()
                finally:
                    await self._track_concurrency_exit()

        if timeout is not None:
            return await asyncio.wait_for(_wrapped(), timeout=timeout)
        else:
            return await _wrapped()

@pytest.mark.asyncio
async def test_concurrency_limit_and_50_requests():
    dispatcher = TaskDispatcher(max_concurrency=5)
    
    async def simulated_task(task_id: int):
        await asyncio.sleep(0.02)
        return f"result_{task_id}"

    tasks = [dispatcher.run_task(lambda tid=i: simulated_task(tid)) for i in range(50)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 50
    assert dispatcher.max_observed_concurrency <= 5
    print(f"\n[SUCESSO] 50 requisições processadas. Concorrência máxima observada: {dispatcher.max_observed_concurrency}")

@pytest.mark.asyncio
async def test_granular_timeout_including_queue():
    dispatcher = TaskDispatcher(max_concurrency=1)

    # Ocupa o único slot do semáforo
    async with dispatcher.semaphore:
        async def slow_task():
            await asyncio.sleep(0.5)
            return "should_not_run"

        start_time = time.time()
        # Como o semáforo está ocupado e o timeout é curto, deve estourar o timeout na fila
        with pytest.raises(asyncio.TimeoutError):
            await dispatcher.run_task(slow_task, timeout=0.05)
        
        duration = time.time() - start_time
        # O timeout deve ocorrer rapidamente (bem antes de 0.5s)
        assert duration < 0.2

    print(f"\n[SUCESSO] Timeout de fila granular capturado em {duration:.4f}s.")

@pytest.mark.asyncio
async def test_exception_safety_releases_semaphore():
    dispatcher = TaskDispatcher(max_concurrency=2)

    async def failing_task():
        raise ValueError("Erro interno na tarefa")

    with pytest.raises(ValueError, match="Erro interno na tarefa"):
        await dispatcher.run_task(failing_task)

    # O semáforo deve estar totalmente disponível (valor 2) mesmo após falha
    assert dispatcher.semaphore._value == 2
    print("\n[SUCESSO] Exceção interna tratada e semáforo garantidamente liberado.")