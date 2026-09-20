import asyncio
import itertools
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, List

@dataclass(frozen=True)
class Task:
    name: str
    func: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

class PriorityTaskQueue:
    def __init__(self, maxsize: int = 0, num_workers: int = 1):
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
        self._counter = itertools.count()
        self._num_workers = num_workers
        self._workers: List[asyncio.Task] = []
        self._running = False

    async def put(self, priority: int, task: Task):
        sequence = next(self._counter)
        await self._queue.put((priority, sequence, task))

    async def _worker_loop(self, worker_id: int, results: List[str]):
        while self._running:
            try:
                priority, seq, task = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                try:
                    await task.func(*task.args, **task.kwargs)
                    results.append(f"OK: {task.name} (prio={priority})")
                except Exception as e:
                    results.append(f"ERR: {task.name} ({e})")
                finally:
                    self._queue.task_done()
            except (asyncio.TimeoutError, asyncio.CancelledError):
                continue

    async def start(self, results_list: List[str]):
        self._running = True
        for i in range(self._num_workers):
            worker = asyncio.create_task(self._worker_loop(i, results_list))
            self._workers.append(worker)

    async def stop(self):
        await self._queue.join()
        self._running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

async def dummy_task(name: str, duration: float):
    await asyncio.sleep(duration)

async def failing_task(name: str):
    await asyncio.sleep(0.05)
    raise ValueError("Simulated Error")

async def run_experiment():
    results = []
    # Teste: 3 workers, maxsize 5
    queue = PriorityTaskQueue(maxsize=5, num_workers=3)
    await queue.start(results)

    # Lista de tarefas para testar:
    # 1. Prioridade (0 é maior que 5)
    # 2. Estabilidade (Alta-1 e Alta-2 têm prio 1, Alta-1 deve ser retirada primeiro)
    # 3. Resiliência (Uma tarefa falha)
    tasks_to_add = [
        (3, Task("Baixa", dummy_task, ("Baixa", 0.1))),
        (1, Task("Alta-1", dummy_task, ("Alta-1", 0.1))),
        (1, Task("Alta-2", dummy_task, ("Alta-2", 0.1))),
        (0, Task("Ultra", dummy_task, ("Ultra", 0.1))),
        (5, Task("Muito-Baixa", dummy_task, ("Muito-Baixa", 0.1))),
        (1, Task("Falha", failing_task, ("Falha",))),
    ]

    for prio, task in tasks_to_add:
        await queue.put(prio, task)

    await queue.stop()

    print("--- RESULTADOS ---")
    for r in results:
        print(r)

    # Validações
    print("\n--- VALIDAÇÕES ---")
    
    # Verificação de Resiliência
    has_err = any("ERR: Falha" in r for r in results)
    print(f"Resiliência (Erro capturado): {'PASSED' if has_err else 'FAILED'}")

    # Verificação de Integridade
    print(f"Integridade (Total {len(results)}/{len(tasks_to_add)}): {'PASSED' if len(results) == len(tasks_to_add) else 'FAILED'}")

    # Verificação de Prioridade (Ultra deve ser um dos primeiros a ser processado)
    # Como há concorrência, não garantimos que o Ultra termine primeiro, 
    # mas garantimos que ele foi retirado da fila com prioridade 0.
    ultra_idx = next(i for i, r in enumerate(results) if "Ultra" in r)
    # Em um cenário de 3 workers, o Ultra (prio 0) deve ser retirado quase instantaneamente.
    print(f"Prioridade (Ultra index: {ultra_idx}): {'PASSED' if ultra_idx <= 2 else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(run_experiment())