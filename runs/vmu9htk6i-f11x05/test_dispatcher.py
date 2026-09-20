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
        """Executa uma corrotina respeitando o limite do semáforo e timeout granular."""
        await self.semaphore.acquire()
        try:
            await self._track_concurrency_enter()
            if timeout is not None:
                return await asyncio.wait_for(coro_func(), timeout=timeout)
            else:
                return await coro_func()
        finally:
            await self._track_concurrency_exit()
            self.semaphore.release()

@pytest.mark.asyncio
async def test_concurrency_limit_and_50_requests():
    dispatcher = TaskDispatcher(max_concurrency=5)
    
    async def simulated_task(task_id: int):
        # Simula I/O com tempo variável
        await asyncio.sleep(0.02)
        return f"result_{task_id}"

    # Dispara 50 tarefas concorrentes
    tasks = [dispatcher.run_task(lambda tid=i: simulated_task(tid)) for i in range(50)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 50
    assert dispatcher.max_observed_concurrency <= 5
    print(f"\n[SUCESSO] 50 requisições processadas. Concorrência máxima observada: {dispatcher.max_observed_concurrency}")

@pytest.mark.asyncio
async def test_granular_timeout():
    dispatcher = TaskDispatcher(max_concurrency=5)

    async def slow_task():
        await asyncio.sleep(0.5)
        return "should_not_finish"

    # Deve disparar TimeoutError devido ao timeout estrito de 0.05s
    start_time = time.time()
    with pytest.raises(asyncio.TimeoutError):
        await dispatcher.run_task(slow_task, timeout=0.05)
    
    duration = time.time() - start_time
    # Garante que o semáforo foi liberado corretamente após o timeout
    assert dispatcher.semaphore._value == 5
    print(f"\n[SUCESSO] Timeout granular capturado em {duration:.4f}s e semáforo liberado com sucesso.")

@pytest.mark.asyncio
async def test_exception_safety_releases_semaphore():
    dispatcher = TaskDispatcher(max_concurrency=2)

    async def failing_task():
        raise ValueError("Erro interno na tarefa")

    with pytest.raises(ValueError, match="Erro interno na tarefa"):
        await dispatcher.run_task(failing_task)

    # O semáforo deve estar totalmente disponível (valor 2) mesmo após falha na corrotina
    assert dispatcher.semaphore._value == 2
    print("\n[SUCESSO] Exceção interna tratada e semáforo garantidamente liberado via finally.")