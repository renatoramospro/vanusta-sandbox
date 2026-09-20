import asyncio
import heapq
import time
import threading
from typing import Callable, Dict, List, Any, Union, Coroutine
from dataclasses import dataclass, field

@dataclass
class EventBusMetrics:
    events_published: int = 0
    handlers_registered: int = 0
    dispatch_errors: int = 0
    total_dispatch_time_ms: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        if self.events_published == 0:
            return 0.0
        return self.total_dispatch_time_ms / self.events_published

@dataclass(order=True)
class HandlerRegistration:
    priority: int
    counter: int = field(compare=True)
    callback: Callable[..., Any] = field(compare=False)
    is_async: bool = field(compare=False)

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[HandlerRegistration]] = {}
        self._lock = threading.RLock()
        self._counter = 0
        self.metrics = EventBusMetrics()

    def subscribe(self, event_type: str, priority: int = 10) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator para registrar handlers síncronos ou assíncronos."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            is_async = asyncio.iscoroutinefunction(func)
            with self._lock:
                self._counter += 1
                reg = HandlerRegistration(
                    priority=priority,
                    counter=self._counter,
                    callback=func,
                    is_async=is_async
                )
                if event_type not in self._handlers:
                    self._handlers[event_type] = []
                
                heapq.heappush(self._handlers[event_type], reg)
                self.metrics.handlers_registered += 1
            return func
        return decorator

    async def publish(self, event_type: str, *args: Any, **kwargs: Any) -> None:
        """Despacha um evento de forma assíncrona para todos os handlers registrados."""
        start_time = time.perf_counter()
        
        with self._lock:
            self.metrics.events_published += 1
            # Cópia defensiva da heap para evitar mutação durante o despacho
            regs = list(self._handlers.get(event_type, []))

        loop = asyncio.get_running_loop()

        for reg in regs:
            try:
                if reg.is_async:
                    await reg.callback(*args, **kwargs)
                else:
                    # Executa handler sync em pool de threads para não bloquear o loop
                    await loop.run_in_executor(None, lambda: reg.callback(*args, **kwargs))
            except Exception as e:
                with self._lock:
                    self.metrics.dispatch_errors += 1
                # Tratamento de erro robusto: propaga ou loga sem interromper demais handlers
                # Aqui optamos por registrar na métrica e continuar a cadeia

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        with self._lock:
            self.metrics.total_dispatch_time_ms += elapsed_ms