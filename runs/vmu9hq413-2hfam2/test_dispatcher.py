import asyncio
import pytest
from dispatcher import TaskDispatcher

class ConcurrencyMonitor:
    """Auxiliar para monitorar o pico de concorrência durante os testes."""
    def __init__(self):
        self.active_tasks = 0
        self.max_observed = 0
        self.lock = asyncio.Lock()

    async def track(self, duration: float, fail_with: Exception = None):
        async with self.lock:
            self.active_tasks += 1
            if self.active_tasks > self.max_observed:
                self.max_observed = self.active_tasks
        
        try:
            await asyncio.sleep(duration)
            if fail_with:
                raise fail_with
        finally:
            async with self.lock:
                self.active_tasks -= 1

@pytest.mark.asyncio
async def test_concurrency_limit():
    """Verifica se o limite de 5 tarefas simultâneas é estritamente respeitado."""
    limit = 5
    total_tasks = 50
    dispatcher = TaskDispatcher(max_concurrency=limit)
    monitor = ConcurrencyMonitor()

    # Criamos 50 tarefas que duram 0.1s
    tasks = [
        dispatcher.dispatch(monitor.track(0.1), timeout=1.0)
        for _ in range(total_tasks)
    ]
    
    await asyncio.gather(*tasks)
    
    assert monitor.max_observed <= limit, f"Limite excedido! Máximo observado: {monitor.max_observed}"
    assert monitor.max_observed > 0

@pytest.mark.asyncio
async def test_timeout_handling():
    """Verifica se o timeout granular funciona e cancela a tarefa."""
    dispatcher = TaskDispatcher(max_concurrency=5)
    monitor = ConcurrencyMonitor()

    # Tarefa que demora 1s, mas o timeout é de 0.1s
    with pytest.raises(asyncio.TimeoutError):
        await dispatcher.dispatch(monitor.track(1.0), timeout=0.1)
    
    # Garantir que a tarefa foi cancelada e não ficou rodando (o monitor deve zerar)
    await asyncio.sleep(1.1)
    assert monitor.active_tasks == 0

@pytest.mark.asyncio
async def test_exception_handling_and_semaphore_release():
    """Verifica se falhas em tarefas liberam o semáforo para as próximas."""
    dispatcher = TaskDispatcher(max_concurrency=2)
    monitor = ConcurrencyMonitor()

    # 1. Disparamos 2 tarefas que falham imediatamente
    tasks = [
        dispatcher.dispatch(monitor.track(0.01, fail_with=ValueError("Erro")), timeout=1.0)
        for _ in range(2)
    ]
    
    for t in tasks:
        with pytest.raises(ValueError):
            await t

    # 2. Se o semáforo não vazou, a próxima tarefa ficará travada para sempre.
    # Vamos tentar rodar uma tarefa de sucesso.
    try:
        await asyncio.wait_for(
            dispatcher.dispatch(monitor.track(0.01), timeout=1.0), 
            timeout=0.5
        )
    except asyncio.TimeoutError:
        pytest.fail("O semáforo vazou! A tarefa de sucesso não conseguiu rodar após as falhas.")

@pytest.mark.asyncio
async def test_cancellation():
    """Verifica se o cancelamento externo da tarefa de despacho é propagado."""
    dispatcher = TaskDispatcher(max_concurrency=5)
    monitor = ConcurrencyMonitor()

    # Criamos uma tarefa de despacho que demora muito
    task = asyncio.create_task(
        dispatcher.dispatch(monitor.track(2.0), timeout=5.0)
    )

    # Deixamos ela começar
    await asyncio.sleep(0.1)
    
    # Cancelamos a tarefa de despacho
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    
    # Verificamos se a tarefa interna também foi limpa
    await asyncio.sleep(2.1)
    assert monitor.active_tasks == 0