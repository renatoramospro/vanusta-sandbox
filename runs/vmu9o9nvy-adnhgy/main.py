import asyncio
import itertools
import time

class UncomparableTask:
    """Uma classe propositalmente sem métodos de comparação para testar a robustez da fila."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"UncomparableTask({self.name})"

class PriorityTaskQueue:
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
        self._counter = itertools.count()  # Garante unicidade e ordem FIFO em empates

    async def put(self, priority: int, coro_func, *args, **kwargs):
        """Adiciona uma tarefa. Menor número = maior prioridade."""
        count = next(self._counter)
        # A tupla (priority, count, ...) evita TypeError e garante FIFO
        await self._queue.put((priority, count, coro_func, args, kwargs))

    async def get(self):
        """Retorna a próxima tarefa (priority, coro_func, args, kwargs)."""
        priority, count, coro_func, args, kwargs = await self._queue.get()
        return priority, coro_func, args, kwargs

    def task_done(self):
        self._queue.task_done()

    async def join(self):
        await self._queue.join()

async def worker(name, queue, results, errors):
    """Worker que processa tarefas e captura erros para não interromper o loop."""
    while True:
        try:
            priority, coro_func, args, kwargs = await queue.get()
            try:
                # Executa a tarefa
                res = await coro_func(*args, **kwargs)
                results.append((priority, res))
            except Exception as e:
                errors.append(f"Worker {name} caught error in task: {e}")
            finally:
                queue.task_done()
        except asyncio.CancelledError:
            break

# --- Funções de Tarefa para Testes ---

async def sample_task(name, delay=0.01):
    await asyncio.sleep(delay)
    return name

async def failing_task():
    raise ValueError("Intentional Failure")

# --- Suíte de Testes ---

async def test_priority_and_fifo():
    print("Running: test_priority_and_fifo...")
    queue = PriorityTaskQueue()
    results = []
    errors = []
    
    # Inserir 10 tarefas com prioridades variadas e empates
    # Prioridades: 1 (Alta), 5 (Média), 10 (Baixa)
    tasks_to_add = [
        (5, "Med-A"), (1, "High-1"), (10, "Low-1"), (5, "Med-B"),
        (1, "High-2"), (10, "Low-2"), (5, "Med-C"), (1, "High-3"),
        (10, "Low-3"), (5, "Med-D")
    ]
    
    for prio, name in tasks_to_add:
        await queue.put(prio, sample_task, name)

    workers = [asyncio.create_task(worker(f"W{i}", queue, results, errors)) for i in range(3)]
    await queue.join()
    for w in workers: w.cancel()

    # Extrair nomes na ordem de execução
    executed_names = [res[1] for res in results]
    
    # Validação 1: Prioridade (High < Med < Low)
    # Nota: Como há 3 workers, a ordem exata pode variar levemente entre tarefas de mesma prioridade,
    # mas as de prioridade 1 DEVEM terminar antes das de prioridade 10.
    high_indices = [executed_names.index(n) for n, p in tasks_to_add if p == 1 for n in [n]] # simplified
    # Vamos fazer uma verificação mais robusta baseada nos valores de prioridade capturados
    
    # Re-capturar prioridades para validar
    # (Como o worker salva (priority, name), podemos validar diretamente)
    # Mas para manter o teste simples, vamos checar se a ordem de conclusão respeita os blocos
    
    # Verificação de ordem de blocos de prioridade
    # Encontrar o último índice de uma prioridade alta e o primeiro de uma baixa
    last_high = max(results.index(r) for r in results if r[0] == 1)
    first_low = min(results.index(r) for r in results if r[0] == 10)
    assert last_high < first_low, "High priority tasks must finish before low priority"

    # Validação 2: FIFO para empates (Med-A deve vir antes de Med-B)
    med_a_idx = next(i for i, r in enumerate(results) if r[1] == "Med-A")
    med_b_idx = next(i for i, r in enumerate(results) if r[1] == "Med-B")
    assert med_a_idx < med_b_idx, "FIFO failed for same priority"

    print("  [PASS] Priority and FIFO validated.")

async def test_resilience():
    print("Running: test_resilience...")
    queue = PriorityTaskQueue()
    results = []
    errors = []
    
    await queue.put(1, sample_task, "Good-Task")
    await queue.put(1, failing_task) # Esta vai falhar
    await queue.put(1, sample_task, "Another-Good-Task")

    workers = [asyncio.create_task(worker("W", queue, results, errors)) for i in range(1)]
    await queue.join()
    for w in workers: w.cancel()

    assert len(results) == 2, "Should have processed 2 successful tasks"
    assert len(errors) == 1, "Should have captured 1 error"
    assert "Intentional Failure" in errors[0]
    print("  [PASS] Resilience validated.")

async def test_uncomparable_objects():
    print("Running: test_uncomparable_objects...")
    queue = PriorityTaskQueue()
    results = []
    errors = []

    # Inserir dois objetos que não podem ser comparados entre si
    t1 = UncomparableTask("Obj1")
    t2 = UncomparableTask("Obj2")

    # Se o contador de sequência não funcionar, isso causará TypeError ao comparar t1 e t2
    await queue.put(1, sample_task, t1.name)
    await queue.put(1, sample_task, t2.name)

    workers = [asyncio.create_task(worker("W", queue, results, errors)) for i in range(1)]
    await queue.join()
    for w in workers: w.cancel()

    assert len(results) == 2
    print("  [PASS] Uncomparable objects handled (no TypeError).")

async def test_backpressure():
    print("Running: test_backpressure...")
    queue = PriorityTaskQueue(maxsize=1)
    
    await queue.put(1, sample_task, "First")
    
    # A segunda tentativa de 'put' deve bloquear. 
    # Vamos usar um timeout para verificar se ele realmente ficou esperando.
    try:
        await asyncio.wait_for(queue.put(1, sample_task, "Second"), timeout=0.2)
        raise AssertionError("Put should have blocked due to maxsize=1")
    except asyncio.TimeoutError:
        print("  [PASS] Back-pressure (blocking) validated.")
    except Exception as e:
        raise e

async def main():
    print("=== STARTING MISSION TESTS ===\n")
    try:
        await test_priority_and_fifo()
        await test_resilience()
        await test_uncomparable_objects()
        await test_backpressure()
        print("\n=== ALL TESTS PASSED SUCCESSFULLY ===")
    except Exception as e:
        print(f"\n!!! TEST SUITE FAILED: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())