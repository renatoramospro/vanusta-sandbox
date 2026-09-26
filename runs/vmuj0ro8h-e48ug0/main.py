import asyncio
import time

class AsyncReactiveBuffer:
    """
    Buffer reativo assíncrono com High/Low Watermark para controle de backpressure.
    Implementa o padrão non-blocking produtor-consumidor.
    """
    def __init__(self, high_watermark: int = 10, low_watermark: int = 3):
        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self.queue = asyncio.Queue()
        self.is_paused = False
        self.paused_events = []
        self.metrics = {"produced": 0, "consumed": 0, "pauses": 0, "resumes": 0}
        self.error = None

    async def produce(self, item):
        """Método chamado pelo produtor. Se o buffer atingir o high watermark, aguarda (não-bloqueante)."""
        if self.error:
            raise self.error

        # Se o buffer estiver cheio, o produtor precisa aguardar a drenagem
        if self.queue.qsize() >= self.high_watermark and not self.is_paused:
            self.is_paused = True
            self.metrics["pauses"] += 1
            print(f"[BACKPRESSURE] High watermark atingido ({self.queue.qsize()} itens). Pausando produtor.")

        while self.is_paused:
            # Espera ativa/assíncrona até que o consumo baixe o buffer
            await asyncio.sleep(0.01)

        await self.queue.put(item)
        self.metrics["produced"] += 1

    async def consume(self):
        """Método chamado pelo consumidor para puxar itens do buffer."""
        while self.queue.empty() and not self.error:
            await asyncio.sleep(0.01)

        if self.error:
            raise self.error

        item = await self.queue.get()
        self.metrics["consumed"] += 1

        # Verifica se atingiu o low watermark para retomar o produtor
        if self.is_paused and self.queue.size <= self.low_watermark if hasattr(self.queue, 'size') else self.queue.qsize() <= self.low_watermark:
            self.is_paused = False
            self.metrics["resumes"] += 1
            print(f"[BACKPRESSURE] Low watermark atingido ({self.queue.qsize()} itens). Retomando produtor.")

        return item

    def set_error(self, err: Exception):
        """Propaga erros do consumidor para o produtor."""
        self.error = err


async def run_pipeline():
    # Buffer com limite estrito para demonstração
    buffer = AsyncReactiveBuffer(high_watermark=5, low_watermark=2)

    # Produtor rápido gerando 15 itens rapidamente
    async def fast_producer():
        try:
            for i in range(15):
                await buffer.produce(f"dado-{i}")
                print(f"Produzido: dado-{i} (Tamanho do buffer: {buffer.queue.qsize()})")
                await asyncio.sleep(0.005) # Produtor muito rápido
        except Exception as e:
            print(f"Produtor interrompido por erro: {e}")

    # Consumidor lento processando 1 item a cada 0.05 segundos
    async def slow_consumer():
        try:
            for _ in range(15):
                await asyncio.sleep(0.05) # Consumidor lento
                item = await buffer.consume( )
                print(f"--> Consumido: {item} (Tamanho do buffer: {buffer.queue.qsize()})")
        except Exception as e:
            print(f"Consumidor encontrou erro: {e}")

    # Executa produtor e consumidor concorrentemente
    await asyncio.gather(fast_producer(), slow_consumer())

    print("\n--- Métricas Finais do Pipeline ---")
    print(buffer.metrics)

    # Asserts para garantir o funcionamento correto do backpressure
    assert buffer.metrics["pauses"] > 0, "O backpressure falhou em pausar o produtor!"
    assert buffer.metrics["resumes"] > 0, "O backpressure falhou em retomar o produtor!"
    print("\n[SUCESSO] Teste de Backpressure executado com observabilidade e sem estouro de memória!")

if __name__ == "__main__":
    asyncio.run(run_pipeline())