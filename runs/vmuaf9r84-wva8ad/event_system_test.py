import pytest
import time
import gc
from event_system import RobustEventBus

class MockSystem:
    def __init__(self, name):
        self.name = name
        self.call_count = 0
        self.received_data = None

    def on_event(self, data):
        self.call_count += 1
        self.received_data = data

class MutationSystem(MockSystem):
    """Sistema que se desinscreve assim que recebe um evento."""
    def __init__(self, name, bus):
        super().__init__(name)
        self.bus = bus

    def on_event(self, data):
        super().on_event(data)
        self.bus.unsubscribe("EVENT", self.on_event)

def test_memory_leak_prevention():
    bus = RobustEventBus()
    system = MockSystem("Target")
    
    bus.subscribe("EVENT", system.on_event)
    
    # Garantir que a referência existe
    bus.publish("EVENT", "data")
    assert system.call_count == 1
    
    # Deletar o objeto e forçar GC
    del system
    gc.collect()
    
    # O publish deve limpar a referência morta sem crashar
    bus.publish("EVENT", "data")
    # Se chegou aqui sem erro, passou.

def test_performance_stress():
    bus = RobustEventBus()
    system = MockSystem("Stress")
    bus.subscribe("STRESS", system.on_event)
    
    iterations = 1000
    start_time = time.perf_counter()
    
    for i in range(iterations):
        bus.publish("STRESS", f"payload_{i}")
        
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print(f"\nTempo para {iterations} eventos: {duration:.4f}s")
    assert system.call_count == iterations
    assert duration < 0.05 # Critério de performance

def test_mutation_during_publish():
    """Testa se o sistema sobrevive a um assinante se desinscrevendo durante o publish."""
    bus = RobustEventBus()
    
    sys1 = MutationSystem("Mutator", bus)
    sys2 = MockSystem("Observer")
    
    bus.subscribe("EVENT", sys1.on_event)
    bus.subscribe("EVENT", sys2.on_event)
    
    # sys1 vai se desinscrever ao receber o evento. 
    # Se o bus não usar cópia, sys2 pode ser pulado.
    bus.publish("EVENT", "data")
    
    assert sys1.call_count == 1
    assert sys2.call_count == 1 # sys2 DEVE receber o evento

def test_lambda_support():
    bus = RobustEventBus()
    received = []
    
    # Teste de lambda (função pura)
    bus.subscribe("LAMBDA", lambda data: received.append(data))
    bus.publish("LAMBDA", "hello")
    
    assert "hello" in received

if __name__ == "__main__":
    pytest.main([__file__])