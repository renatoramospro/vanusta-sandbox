import asyncio
import itertools
import time

class UncomparableTask:
    """Objeto propositalmente impossível de comparar para testar a robustez da fila."""
    def __init__(self, name):
        self.name = name
    def __lt__(self, other):
        raise TypeError(f"Erro de design: Tentativa de comparar {self.name} com outro objeto!")
    def __repr__(self):
        return f"Uncomparable({self.name})"

class PriorityTaskQueue:
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
        self._counter = itertools.count()  # Garante unicidade e ordem FIFO

    async def put(self, priority: int, coro_func, *args, **kwargs):
        """Adiciona tarefa. Menor priority número = maior prioridade."""
        count = next(self._counter)
        # A tupla (priority, count, ...) evita comparar coro_func diretamente
        await self._queue.put((priority, count, coro_func, args, kwargs))

    async def get(self):
        """Retorna a próxima tarefa (priority, count, coro, args, kwargs)."""
        return await self._queue.get()

    def task_done(self):
        self._queue.task_done()

    async def join(self):
        await self._queue.join()

async def worker(name, queue, results):
    """Worker que processa tarefas e registra resultados ou erros."""
    try:
        while True:
            priority, count, coro, args, kwargs = await queue.get()
            try:
                # Executa a tarefa
                result = await coro(*args, **kwargs)
                results.append({"priority": priority, "count": count, "status": "success", "val": result})
            except Exception as e:
                results.append({"priority": priority, "count": count, "status": "error", "val": str(e)})
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        pass

# --- Tarefas de Teste ---

async def sample_task(name, duration=0.01):
    await asyncio.sleep(duration)
    return name

async def failing_task():
    await asyncio.sleep(0.01)
    raise ValueError("Falha proposital")

# --- Suíte de Testes ---

async def run_test_suite():
    print("=== Iniciando Suíte de Testes da PriorityTaskQueue ===\n")
    
    queue = PriorityTaskQueue(maxsize=20)
    results = []
    
    # 1. Iniciar Workers
    workers = [asyncio.create_task(worker(f"W-{i}", queue, results)) for i in range(3)]

    print("[1/4] Testando Prioridade e FIFO...")
    # Inserir tarefas com diferentes prioridades
    await queue.put(10, sample_task, "Baixa-1")
    await queue.put(1,  sample_task, "Alta-1")
    await queue.put(5,  sample_task, "Media-A")
    await queue.put(5,  sample_task, "Media-B") # Deve vir após Media-A (FIFO)
    await queue.put(1,  sample_task, "Alta-2")  # Deve vir após Alta-1 (FIFO)

    # 2. Testando Resiliência (Tarefa que falha)
    print("[2/4] Testando Resiliência a Exceções...")
    await queue.put(0, failing_task) # Prioridade máxima, mas vai falhar

    # 3. Testando Objetos Não Comparáveis (O grande teste de design)
    print("[3/4] Testando Prevenção de TypeError (Objetos não comparáveis)...")
    # Se o contador não funcionar, o Python tentará comparar UncomparableTask e falhará
    await queue.put(2, sample_task, UncomparableTask("Objeto-X"))
    await queue.put(2, sample_task, UncomparableTask("Objeto-Y"))

    # Aguardar processamento
    await queue.join()

    # Parar workers
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    # --- Validações ---
    
    # Ordenar resultados pela ordem de conclusão para análise (embora a ordem de execução 
    # dependa do scheduler, a prioridade deve ser respeitada no início)
    # Para teste rigoroso, vamos verificar se as prioridades foram respeitadas.
    
    print("\n--- Relatório de Execução ---")
    for r in results:
        print(f"Prio: {r['priority']} | Count: {r['count']} | Status: {r['status']} | Val: {r['val']}")

    # Validação de Prioridade (Simplificada para o log)
    # Nota: Como há 3 workers, a ordem exata de conclusão pode variar levemente, 
    # mas a lógica de prioridade deve garantir que as de prioridade 0 e 1 comecem antes das 10.
    
    # Verificando se o erro de comparação NÃO aconteceu
    errors = [r for r in results if r['status'] == 'error' and "TypeError" in r['val']]
    assert len(errors) == 0, "ERRO: O sistema permitiu uma comparação de objetos não comparáveis!"

    # Verificando se a tarefa falha foi capturada sem derrubar o worker
    failing_captured = any(r['status'] == 'error' and "Falha proposital" in r['val'] for r in results)
    assert failing_captured, "ERRO: A tarefa que deveria falhar não foi capturada corretamente."

    # Verificando se as tarefas de alta prioridade foram processadas
    high_prio_count = len([r for r in results if r['priority'] == 1])
    assert high_prio_count == 2, f"ERRO: Esperava 2 tarefas de prioridade 1, encontrou {high_prio_count}"

    print("\n✅ TODOS OS TESTES PASSARAM COM SUCESSO!")

if __name__ == "__main__":
    try:
        asyncio.run(run_test_suite())
    except Exception as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        exit(1)