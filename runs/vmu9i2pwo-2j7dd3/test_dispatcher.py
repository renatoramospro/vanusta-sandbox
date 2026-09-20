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
        O timeout agora envolve a tentativa de aquisição do semáforo (timeout de fila)
        e a execução da tarefa.
        """
        async def _guarded_execution():
            # O 'async with' garante a liberação do semáforo mesmo se houver cancelamento
            # ou erro durante a execução da tarefa ou das métricas.
            async with self.semaphore:
                await self._track_concurrency_enter()
                try:
                    return await coro_func()
                finally:
                    # Usamos um try/except aqui para garantir que a falha de uma métrica
                    # não impeça o funcionamento do sistema, mas o semáforo já está
                    # protegido pelo 'async with' externo.
                    try:
                        await self._track_concurrency_exit()
                    except Exception:
                        pass 

        if timeout is not None:
            # O wait_for envolve o processo completo: esperar semáforo + executar
            return await asyncio.wait_for(_guarded_execution(), timeout=timeout)
        else:
            return await _guarded_execution()

@pytest.mark.asyncio
async def test_concurrency_limit_and_50_requests():
    dispatcher = TaskDispatcher(max_concurrency=5)
    
    async def simulated_task(task_id: int):
        await asyncio.sleep(0.01)
        return f"result_{task_id}"

    # Dispara 50 tarefas
    tasks = [dispatcher.run_task(lambda tid=i: simulated_task(tid)) for i in range(50)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 50
    assert dispatcher.max_observed_concurrency <= 5
    print(f"\n[SUCESSO] 50 requisições processadas. Concorrência máxima: {dispatcher.max_observed_concurrency}")

@pytest.mark.asyncio
async def test_granular_timeout_and_queue_wait():
    """Valida que o timeout cobre o tempo de espera na fila do semáforo."""
    dispatcher = TaskDispatcher(max_concurrency=1)

    async def slow_task():
        await asyncio.sleep(0.5)
        return "done"

    # Primeira tarefa ocupa o semáforo
    t1 = asyncio.create_task(dispatcher.run_task(slow_task))
    await asyncio.sleep(0.05) # Garante que t1 pegou o semáforo

    # Segunda tarefa tentará pegar o semáforo, mas o timeout é curto (0.1s)
    # Como t1 demora 0.5s, t2 deve sofrer timeout enquanto espera na fila.
    start_time = time.time()
    with pytest.raises(asyncio.TimeoutError):
        await dispatcher.run_task(slow_task, timeout=0.1)
    
    duration = time.time() - start_time
    assert duration < 0.3 # Deve falhar rápido por causa do timeout
    
    await t1 # Limpa a primeira tarefa
    # Verifica se o semáforo foi liberado para novas tarefas
    assert dispatcher.semaphore._value == 1
    print(f"\n[SUCESSO] Timeout de fila funcionou. Semáforo íntegro.")

@pytest.mark.asyncio
async def test_exception_safety_releases_semaphore():
    """Valida que falhas na tarefa ou nas métricas não vazam o semáforo."""
    dispatcher = TaskDispatcher(max_concurrency=2)

    async def failing_task():
        raise ValueError("Erro interno")

    with pytest.raises(ValueError, match="Erro interno"):
        await dispatcher.run_task(failing_task)

    # O semáforo deve estar disponível (valor 2)
    assert dispatcher.semaphore._value == 2
    print("\n[SUCESSO] Exceção tratada e semáforo liberado via 'async with'.")

@pytest.mark.asyncio
async def test_cancellation_safety():
    """Valida que o cancelamento externo não causa vazamento."""
    dispatcher = TaskDispatcher(max_concurrency=1)

    async def long_task():
        await asyncio.sleep(10)
        return "finished"

    task = asyncio.create_task(dispatcher.run_task(long_task))
    await asyncio.sleep(0.05) # Deixa a tarefa entrar
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    # Mesmo com cancelamento, o semáforo deve ser liberado pelo context manager
    assert dispatcher.semaphore._value == 1
    print("\n[SUCESSO] Cancelamento externo tratado sem vazamento.")