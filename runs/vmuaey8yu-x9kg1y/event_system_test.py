import pytest
import gc
from event_system import RobustEventBus, BadEventBus

class MockSystem:
    def __init__(self, name):
        self.name = name
        self.call_count = 0
    def on_event(self, data):
        self.call_count += 1

def test_robustness_and_lambdas():
    bus = RobustEventBus()
    lambda_called = False
    
    def global_func(data):
        nonlocal lambda_called
        lambda_called = True

    # Testando suporte a lambdas e funções globais (Correção do Tester)
    bus.subscribe("TEST", lambda x: None)
    bus.subscribe("TEST", global_func)
    bus.publish("TEST", "data")
    
    assert lambda_called is True

def test_memory_leak_prevention():
    bus = RobustEventBus()
    bad_bus = BadEventBus()
    
    system = MockSystem("Target")
    
    # No RobustBus, ao deletar 'system', a referência fraca morre
    bus.subscribe("EVENT", system.on_event)
    bad_bus.subscribe("EVENT", system.on_event)
    
    del system
    gc.collect() # Força o Garbage Collector
    
    # O RobustBus deve limpar a lista automaticamente ao publicar
    bus.publish("EVENT") 
    assert len(bus._subscribers["EVENT"]) == 0
    
    # O BadBus ainda mantém a referência forte, impedindo o GC de limpar o objeto
    # (Em um teste real de memória, veríamos o tamanho do heap não diminuir)
    assert len(bad_bus._subscribers["EVENT"]) == 1

def test_performance_stress():
    bus = RobustEventBus()
    system = MockSystem("Stress")
    bus.subscribe("STRESS", system.on_event)
    
    start_time = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        bus.publish("STRESS", "payload")
    end_time = time.perf_counter()
    
    duration = end_time - start_time
    print(f"\nTempo para {iterations} eventos: {duration:.4f}s")
    
    assert system.call_count == iterations
    assert duration < 0.05  # Critério de performance (muito abaixo de 16ms)

if __name__ == "__main__":
    # Execução manual para demonstração
    pytest.main([__file__])