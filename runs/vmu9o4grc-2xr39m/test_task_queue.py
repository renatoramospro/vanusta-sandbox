import asyncio
import time
import pytest

class PriorityTaskQueue:
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
        self._counter = 0  # Usado para garantir estabilidade (FIFO) em prioridades iguais
        self._lock = asyncio.Lock()

    async def put(self, priority: int, coro_func, *args, **kwargs):
        """Adiciona uma tarefa à fila com uma prioridade específica (menor número = maior prioridade)."""
        async with self._lock:
            count = self._counter
            self._counter += 1
        
        # A tupla (priority, count, coro_func, args, kwargs) garante que o heapq 
        # ordene por prioridade e, em caso de empate, pela ordem de inserção (count).
        await self._queue.put((priority, count, coro_func, args, kwargs))

    async def get(self):
        """Retorna a próxima tarefa de maior prioridade."""
        priority, count, coro_func, args, kwargs = await self._queue.get()
        return priority, coro_func, args, kwargs

    def task_done(self):
        self._queue.task_done()

    async def join(self):
        await self._queue.join()

    @property
    def qsize(self):
        return self._queue.qsize()


async def worker(worker_id: int, queue: PriorityTaskQueue, results: list):
    while True:
        try:
            priority, coro_func, args, kwargs = await queue.get()
            try:
                res = await coro_func(*args, **kwargs)
                results.append((priority, res))
            except Exception as e:
                results.append((priority, f"ERROR: {e}"))
            finally:
                queue.task_done()
        except asyncio.CancelledError:
            break


@pytest.mark.asyncio
async def test_priority_and_fifo_order():
    queue = PriorityTaskQueue(maxsize=50)
    results = []

    # Mock de função assíncrona para tarefa
    async def sample_task(name: str):
        await asyncio.sleep(0.01)
        return name

    # Inserção fora de ordem
    # Prioridades: 10 (baixa), 1 (alta), 5 (média)
    # Empates na prioridade 5 para testar FIFO
    await queue.put(10, sample_task, "Task-Low-1")
    await queue.put(1, sample_task, "Task-High-1")
    await queue.put(5, sample_task, "Task-Med-A")
    await queue.put(5, sample_task, "Task-Med-B")  # Deve rodar depois da Med-A (FIFO)
    await queue.put(1, sample_task, "Task-High-2")  # Deve rodar depois da High-1 (FIFO)

    # Iniciar 2 workers concorrentes
    workers = [asyncio.create_task(worker(i, queue, results)) for i in range(2)]

    # Aguardar processamento de todas as tarefas
    await queue.join()

    # Cancelar workers
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    # Extrair apenas os nomes dos resultados ordenados por ordem de conclusão/execução
    executed_names = [res[1] for res in results]

    print(f"Ordem de execução real: {executed_names}")

    # Validações estritas:
    # 1. As de alta prioridade (1) devem vir antes das médias (5), que devem vir antes das baixas (10).
    # 2. Dentro da prioridade 5, 'Task-Med-A' deve vir antes de 'Task-Med-B' (FIFO).
    
    high_indices = [executed_names.index("Task-High-1"), executed_names.index("Task-High-2")]
    med_indices = [executed_names.index("Task-Med-A"), executed_names.index("Task-Med-B")]
    low_index = executed_names.index("Task-Low-1")

    assert max(high_indices) < min(med_indices), "Tarefas de alta prioridade devem executar antes das médias"
    assert max(med_indices) < low_index, "Tarefas médias devem executar antes das baixas"
    assert executed_names.index("Task-Med-A") < executed_names.index("Task-Med-B"), "Empates devem respeitar FIFO"
    
    print("Todos os testes de prioridade e ordenação FIFO passaram com sucesso!")


if __name__ == "__main__":
    asyncio.run(test_priority_and_fifo_order())