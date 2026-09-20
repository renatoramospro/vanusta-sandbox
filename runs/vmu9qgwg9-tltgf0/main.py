import asyncio
import time
import inspect
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Type, TypeVar, Union

T = TypeVar("T")

@dataclass
class BusMetrics:
    events_published: int = 0
    handlers_registered: int = 0
    dispatch_errors: int = 0
    total_latency: float = 0.0

    def __str__(self):
        avg_latency = (self.total_latency / self.events_published * 1000) if self.events_published > 0 else 0
        return (f"BusMetrics(events_published={self.events_published}, "
                f"handlers_registered={self.handlers_registered}, "
                f"dispatch_errors={self.dispatch_errors}, "
                f"avg_latency_ms={avg_latency:.6f}ms)")

@dataclass
class Handler(Generic[T]):
    callback: Callable[[T], Any]
    priority: int
    counter: int  # Para garantir FIFO em prioridades iguais

class EventBus(Generic[T]):
    def __init__(self):
        self._handlers: Dict[Type[T], List[Handler[T]]] = {}
        self._lock = threading.RLock()
        self._metrics = BusMetrics()
        self._counter = 0

    def subscribe(self, event_type: Type[T], callback: Callable[[T], Any], priority: int = 0):
        """Registra um handler para um tipo de evento específico."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            self._counter += 1
            handler = Handler(callback=callback, priority=priority, counter=self._counter)
            self._handlers[event_type].append(handler)
            
            # Ordenação: Prioridade decrescente (-priority), depois ordem de registro (counter)
            self._handlers[event_type].sort(key=lambda h: (-h.priority, h.counter))
            
            self._metrics.handlers_registered += 1

    async def publish(self, event: T):
        """Despacha um evento para todos os handlers registrados para o seu tipo."""
        start_time = time.perf_counter()
        event_type = type(event)
        
        # Copiamos a lista de handlers sob lock para permitir thread-safety 
        # sem segurar o lock durante a execução (que pode ser lenta/async)
        with self._lock:
            handlers_to_run = list(self._handlers.get(event_type, []))

        if not handlers_to_run:
            return

        for handler in handlers_to_run:
            try:
                if inspect.iscoroutinefunction(handler.callback):
                    await handler.callback(event)
                else:
                    handler.callback(event)
            except Exception:
                with self._lock:
                    self._metrics.dispatch_errors += 1

        latency = time.perf_counter() - start_time
        with self._lock:
            self._metrics.events_published += 1
            self._metrics.total_latency += latency

    def get_metrics(self) -> BusMetrics:
        with self._lock:
            # Retorna uma cópia para evitar race conditions na leitura
            m = self._metrics
            return BusMetrics(m.events_published, m.handlers_registered, m.dispatch_errors, m.total_latency)

# --- Testes e Experimento ---

@dataclass
class TestEvent:
    data: str

async def run_experiment():
    print("Starting EventBus Mission Experiment...\n")

    # 1. Teste de Prioridade e FIFO
    print("Test 1: Priority and FIFO Order...")
    bus_prio = EventBus[TestEvent]()
    execution_order = []

    def sync_low(ev: TestEvent): execution_order.append("low")
    async def async_high(ev: TestEvent): execution_order.append("high")
    def sync_mid(ev: TestEvent): execution_order.append("mid")
    def sync_fifo_1(ev: TestEvent): execution_order.append("fifo_1")
    def sync_fifo_2(ev: TestEvent): execution_order.append("fifo_2")

    bus_prio.subscribe(TestEvent, sync_low, priority=0)
    bus_prio.subscribe(TestEvent, async_high, priority=10)
    bus_prio.subscribe(TestEvent, sync_mid, priority=5)
    bus_prio.subscribe(TestEvent, sync_fifo_1, priority=5) # Mesma que mid
    bus_prio.subscribe(TestEvent, sync_fifo_2, priority=5) # Mesma que mid

    await bus_prio.publish(TestEvent("prio_test"))
    
    # Ordem esperada: high (10), mid (5), fifo_1 (5), fifo_2 (5), low (0)
    # Nota: mid, fifo_1, fifo_2 têm mesma prioridade, devem seguir ordem de registro
    expected_order = ["high", "mid", "fifo_1", "fifo_2", "low"]
    assert execution_order == expected_order, f"Priority fail: {execution_order}"
    print("✅ Priority and FIFO passed.")

    # 2. Teste de Isolamento de Erros
    print("\nTest 2: Error Isolation...")
    bus_err = EventBus[TestEvent]()
    error_caught = False

    async def failing_handler(ev: TestEvent):
        raise ValueError("Intentional Failure")

    async def successful_handler(ev: TestEvent):
        nonlocal error_caught
        error_caught = True

    bus_err.subscribe(TestEvent, failing_handler, priority=10)
    bus_err.subscribe(TestEvent, successful_handler, priority=5)

    await bus_err.publish(TestEvent("error_test"))
    
    assert error_caught is True, "Successful handler should have run despite previous error"
    assert bus_err.get_metrics().dispatch_errors == 1, "Error should be recorded in metrics"
    print("✅ Error isolation passed.")

    # 3. Teste de Performance (Benchmark)
    print("\nTest 3: Performance Benchmark...")
    bus_perf = EventBus[TestEvent]()
    iterations = 1000
    num_handlers = 10

    # Mix de handlers
    for i in range(num_handlers):
        if i % 2 == 0:
            bus_perf.subscribe(TestEvent, lambda e: None, priority=i)
        else:
            async def async_noop(e): pass
            bus_perf.subscribe(TestEvent, async_noop, priority=i)

    start_time = time.perf_counter()
    for _ in range(iterations):
        await bus_perf.publish(TestEvent("perf_test"))
    end_time = time.perf_counter()

    total_duration = end_time - start_time
    avg_ms_per_event = (total_duration / iterations) * 1000
    metrics = bus_perf.get_metrics()

    print(f"Total time for {iterations} events: {total_duration:.4f}s")
    print(f"Performance: {avg_ms_per_event:.4f}ms per event")
    print(f"Metrics: {metrics}")

    # Critério de sucesso: < 10ms por evento
    assert avg_ms_per_event < 10.0, f"Performance too slow: {avg_ms_per_event}ms"
    assert metrics.events_published == iterations, f"Expected {iterations} events, got {metrics.events_published}"
    print("✅ Performance benchmark passed.")

    print("\n✨ ALL EXPERIMENTS PASSED SUCCESSFULLY ✨")

if __name__ == "__main__":
    asyncio.run(run_experiment())