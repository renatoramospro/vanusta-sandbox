import asyncio
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Type, TypeVar, Union, Awaitable

T = TypeVar("T")

@dataclass
class BusMetrics:
    events_published: int = 0
    handlers_registered: int = 0
    dispatch_errors: int = 0
    total_latency: float = 0.0

    @property
    def average_latency(self) -> float:
        return self.total_latency / self.events_published if self.events_published > 0 else 0.0

@dataclass(order=True)
class Handler(Generic[T]):
    priority: int
    callback: Callable[[T], Union[None, Awaitable[None]]] = field(compare=False)
    is_async: bool = field(compare=False)

class EventBus(Generic[T]):
    def __init__(self):
        self._handlers: Dict[Type[T], List[Handler[T]]] = {}
        self._lock = threading.Lock()
        self._metrics = BusMetrics()
        self._metrics_lock = threading.Lock()

    def subscribe(self, event_type: Type[T], callback: Callable[[T], Any], priority: int = 0):
        is_async = asyncio.iscoroutinefunction(callback)
        # Usamos -priority para que o sort() padrão (ascendente) coloque 
        # os maiores valores primeiro (ex: -10 < -5 < 0)
        handler = Handler(priority=-priority, callback=callback, is_async=is_async)
        
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            self._handlers[event_type].sort()
            
            with self._metrics_lock:
                self._metrics.handlers_registered += 1

    async def publish(self, event: T):
        event_type = type(event)
        start_time = time.perf_counter()
        
        with self._lock:
            handlers_to_run = list(self._handlers.get(event_type, []))

        if not handlers_to_run:
            return

        for handler in handlers_to_run:
            try:
                if handler.is_async:
                    await handler.callback(event)
                else:
                    handler.callback(event)
            except Exception as e:
                with self._metrics_lock:
                    self._metrics.dispatch_errors += 1
                # Em produção, usar logger
                pass 

        latency = time.perf_counter() - start_time
        with self._metrics_lock:
            self._metrics.events_published += 1
            self._metrics.total_latency += latency

    def get_metrics(self) -> BusMetrics:
        with self._metrics_lock:
            return BusMetrics(
                events_published=self._metrics.events_published,
                handlers_registered=self._metrics.handlers_registered,
                dispatch_errors=self._metrics.dispatch_errors,
                total_latency=self._metrics.total_latency
            )

# --- Test Suite ---

@dataclass
class TestEvent:
    data: str

async def run_experiment():
    bus = EventBus[TestEvent]()
    execution_order = []

    # 1. Teste de Prioridade
    async def handler_low(ev: TestEvent): execution_order.append("low")
    async def handler_high(ev: TestEvent): execution_order.append("high")
    async def handler_mid(ev: TestEvent): execution_order.append("mid")

    bus.subscribe(TestEvent, handler_low, priority=0)
    bus.subscribe(TestEvent, handler_high, priority=10)
    bus.subscribe(TestEvent, handler_mid, priority=5)

    await bus.publish(TestEvent("prio_test"))
    assert execution_order == ["high", "mid", "low"]
    execution_order.clear()

    # 2. Teste de Robustez
    async def handler_error(ev: TestEvent): raise ValueError("Boom!")
    async def handler_ok(ev: TestEvent): execution_order.append("ok")

    bus.subscribe(TestEvent, handler_error, priority=10)
    bus.subscribe(TestEvent, handler_ok, priority=5)

    await bus.publish(TestEvent("error_test"))
    assert "ok" in execution_order
    execution_order.clear()

    # 3. Teste de Performance
    bus._handlers.clear()
    def sync_handler(ev: TestEvent): pass
    async def async_handler(ev: TestEvent): pass

    for i in range(5):
        bus.subscribe(TestEvent, sync_handler, priority=i)
        bus.subscribe(TestEvent, async_handler, priority=i)

    iterations = 1000
    start_perf = time.perf_counter()
    for _ in range(iterations):
        await bus.publish(TestEvent("perf_test"))
    end_perf = time.perf_counter()

    total_time = end_perf - start_perf
    avg_time_ms = (total_time / iterations) * 1000
    metrics = bus.get_metrics()

    print(f"Performance: {avg_time_ms:.4f}ms per event")
    print(f"Metrics: {metrics}")
    
    assert avg_time_ms < 10.0
    assert metrics.events_published == iterations
    print("EXPERIMENT PASSED")

if __name__ == "__main__":
    asyncio.run(run_experiment())