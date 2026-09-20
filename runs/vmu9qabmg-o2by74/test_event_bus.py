import asyncio
import pytest
from event_bus import EventBus

@pytest.mark.asyncio
async def test_registration_and_priority_fifo():
    bus = EventBus()
    execution_order = []

    @bus.subscribe("test.event", priority=10)
    def handler_sync_low(val):
        execution_order.append(f"sync_low_{val}")

    @bus.subscribe("test.event", priority=1)
    async def handler_async_high(val):
        execution_order.append(f"async_high_{val}")

    @bus.subscribe("test.event", priority=1)
    def handler_sync_high_fifo_first(val):
        execution_order.append(f"sync_fifo_1_{val}")

    @bus.subscribe("test.event", priority=1)
    def handler_sync_high_fifo_second(val):
        execution_order.append(f"sync_fifo_2_{val}")

    await bus.publish("test.event", "data")

    # Prioridade 1 deve vir antes de 10.
    # Entre os de prioridade 1, a ordem FIFO deve ser respeitada pelo counter.
    assert execution_order == [
        "async_high_data",
        "sync_fifo_1_data",
        "sync_fifo_2_data",
        "sync_low_data"
    ]
    assert bus.metrics.handlers_registered == 4
    assert bus.metrics.events_published == 1

@pytest.mark.asyncio
async def test_error_handling():
    bus = EventBus()
    success_called = []

    @bus.subscribe("error.event", priority=1)
    def failing_sync_handler():
        raise ValueError("Sync failure")

    @bus.subscribe("error.event", priority=2)
    async def failing_async_handler():
        raise RuntimeError("Async failure")

    @bus.subscribe("error.event", priority=3)
    def success_handler():
        success_called.append(True)

    await bus.publish("error.event")

    # Verifica se o erro foi capturado nas métricas e se o handler posterior executou
    assert bus.metrics.dispatch_errors == 2
    assert success_called == [True]

@pytest.mark.asyncio
async def test_performance_benchmark():
    bus = EventBus()

    # Registra 10 handlers mistos
    for i in range(5):
        @bus.subscribe("perf.event", priority=i)
        def dummy_sync():
            pass

        @bus.subscribe("perf.event", priority=i + 5)
        async def dummy_async():
            await asyncio.sleep(0.0001)

    # Despacha 1.000 eventos
    start = asyncio.get_running_loop().time()
    for _ in range(1000):
        await bus.publish("perf.event")
    duration = asyncio.get_running_loop().time() - start

    avg_time_ms = (duration / 1000.0) * 1000.0

    print(f"\nBenchmark: 1000 eventos despachados em {duration:.3f}s")
    print(f"Latência média por evento: {avg_time_ms:.4f}ms")
    print(f"Métricas registradas: {bus.metrics}")

    # Critério ajustado pelo Arquiteto: <= 10ms por evento
    assert avg_time_ms <= 10.0
    assert bus.metrics.events_published == 1000
    assert bus.metrics.dispatch_errors == 0