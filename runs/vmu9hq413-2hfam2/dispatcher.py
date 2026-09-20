import asyncio
from typing import Any, Coroutine

class TaskDispatcher:
    """
    Despachante de tarefas que limita a concorrência e aplica timeouts.
    """
    def __init__(self, max_concurrency: int):
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def dispatch(self, coro: Coroutine, timeout: float) -> Any:
        """
        Executa uma corrotina respeitando o limite de concorrência e o timeout.
        
        O uso de 'async with self.semaphore' garante que a permissão seja 
        liberada mesmo se a corrotina lançar exceção, sofrer timeout ou cancelamento.
        """
        async with self.semaphore:
            # wait_for cancela a corrotina interna se o timeout for atingido
            return await asyncio.wait_for(coro, timeout)