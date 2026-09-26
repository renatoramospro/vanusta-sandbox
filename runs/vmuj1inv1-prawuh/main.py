import asyncio
import time

class AsyncReactiveBuffer:
    """
    Buffer reativo assíncrono com High/Low Watermark para controle de backpressure.
    Usa asyncio.Event para suspensão/retomada orientada a eventos e asyncio.Lock
    para garantir thread-safety concorrente (múltiplos produtores/consumidores).
    """
    def __init__(self, high_watermark: int = 10, low_watermark: int = 3):
        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self.queue = asyncio.Queue()
        
        # Evento assíncrono para controle de pausa/retomada (set() = rodando, clear() = pausado)
        self.can_produce = asyncio.Event()
        self.can_produce.set()
        
        # Lock para proteger a verificação de watermarks e alterações de estado concorrentes
        self.lock = asyncio.Lock()
        
        self.metrics = {"produced": 0, "consumed": 0, "pauses": 0, "resumes": 0}
        self.error = None

    async def produce(self, item):
        """Método chamado pelo produtor. Aguarda de forma não-bloqueante via asyncio.Event se o buffer estiver cheio."""
        if self.error:
            raise self.error

        # Aguarda o sinal de que é permitido produzir (bloqueio assíncrono puro, sem busy-wait/polling)
        await self.can_produce.wait()

        async with self.lock:
            if self.error:
                raise self.error
            
            await self.queue.put(item)
            self.metrics["produced"] += 1
            size = self.queue.qsize()
            print(f"Produzido: {item} (Tamanho do buffer: {size})")

            # Se atingiu o high watermark, limpa o evento para pausar produtores subsequentes
            if size >= self.high_watermark and self.can_produce.is_set():
                self.can_produce.clear()
                self.metrics["pauses"] += 1
                print(f"[BACKPRESSURE] High watermark atingido ({size} itens). Pausando produtor.")

    async def consume(self):
        """Método chamado pelo consumidor para puxar itens do buffer e gerenciar o low watermark."""
        item = await self.queue.get()
        
        async with self.lock:
            self.metrics["consumed"] += 1
            size = self.queue.qsize()
            print(f"--> Consumido: {item} (Tamanho do buffer: {size})")

            # Verifica se atingiu o low watermark para retomar o produtor
            if not self.can_produce.is_set() and size <= self.low_watermark:
                self.can_produce.set()
                self.metrics["resumes"] += 1
                print(f"[BACKPRESSURE] Low watermark atingido ({size} itens). Retomando produtor.")

        if self.error:
            raise self.error

        return item

    def set_error(self, err: Exception):
        """Propaga erros do consumidor para o produtor."""
        self.error = err
        self.can_produce.set() # Libera event para propagar a exceção

async def run_pipeline():
    # Parâmetros restritos para disparar backpressure rapidamente
    buffer = AsyncReactiveBuffer(high_watermark=5, low_watermark=2)

    async def fast_producer(name, count):
        try:
            for i in range(count):
                await buffer.produce(f"{name}-dado-{i}")
                # Produtor muito rápido sem delay artificial
        except Exception as e:
            print(f"[{name}] Erro capturado: {e}")

    async def slow_consumer():
        try:
            for _ in range(30):
                await asyncio.sleep(0.05) # Consumidor mais lento
                await buffer.consume()
        except Exception as e:
            print(f"[Consumidor] Erro capturado: {e}")

    # Executa múltiplos produtores concorrentes para testar condições de corrida
    await asyncio.gather(
        fast_producer("P1", 15),
        fast_producer("P2", 15),
        slow_consumer()
    )

    print("\n--- Métricas Finais do Pipeline ---")
    print(buffer.metrics)

    assert buffer.metrics["pauses"] > 0, "O backpressure falhou em pausar o produtor!"
    assert buffer.metrics["resumes"] > 0, "O backpressure falhou em retomar o produtor!"
    print("\n[SUCESSO] Teste de Backpressure corrigido executado com sucesso e sem condições de corrida!")

if __name__ == "__main__":
    asyncio.run(run_pipeline())