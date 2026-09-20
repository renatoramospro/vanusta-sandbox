import time
import weakref
import gc

# --- IMPLEMENTAÇÃO DO SISTEMA ---

class Event:
    """Classe base para todos os eventos."""
    pass

class ScoreChangedEvent(Event):
    def __init__(self, new_score):
        self.new_score = new_score

class RobustEventBus:
    """
    Sistema de mensageria profissional.
    Usa WeakMethod para evitar Memory Leaks.
    """
    def __init__(self):
        # Dicionário: { TipoDoEvento: [WeakMethod, WeakMethod, ...] }
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # Usamos WeakMethod para que o EventBus não segure o objeto vivo
        if hasattr(callback, '__self__'):
            self._subscribers[event_type].append(weakref.WeakMethod(callback))
        else:
            # Para funções puras (não métodos), usamos ref simples
            self._subscribers[event_type].append(weakref.ref(callback))

    def publish(self, event: Event):
        event_type = type(event)
        if event_type not in self._subscribers:
            return

        # Filtramos assinantes que ainda existem (limpeza in-place)
        still_alive = []
        for ref in self._subscribers[event_type]:
            callback = ref()
            if callback is not None:
                callback(event)
                still_alive.append(ref)
        
        self._subscribers[event_type] = still_alive

class BadEventBus:
    """
    Implementação errada que causa Memory Leaks.
    Mantém referências fortes aos métodos dos objetos.
    """
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback) # Referência FORTE

    def publish(self, event: Event):
        event_type = type(event)
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(event)

# --- COMPONENTES DO JOGO ---

class UISystem:
    def __init__(self, name):
        self.name = name
        self.score = 0
    
    def on_score_changed(self, event: ScoreChangedEvent):
        self.score = event.new_score
        # print(f"[{self.name}] UI Atualizada: {self.score}")

class GameplaySystem:
    def __init__(self, bus: RobustEventBus):
        self.bus = bus
        self.score = 0

    def add_score(self, amount):
        self.score += amount
        self.bus.publish(ScoreChangedEvent(self.score))

# --- TESTES ---

def test_performance_and_leaks():
    print("--- Iniciando Testes de Missão ---")
    
    # 1. Teste de Performance (1000 eventos/frame)
    bus = RobustEventBus()
    ui = UISystem("MainUI")
    gameplay = GameplaySystem(bus)
    bus.subscribe(ScoreChangedEvent, ui.on_score_changed)

    start_time = time.perf_counter()
    for i in range(1000):
        gameplay.add_score(1)
    end_time = time.perf_counter()
    
    duration_ms = (end_time - start_time) * 1000
    print(f"[PERFORMANCE] 1000 eventos processados em: {duration_ms:.4f}ms")
    assert duration_ms < 50, "Performance muito baixa para 1000 eventos"

    # 2. Teste de Memory Leak (O ponto crucial)
    print("\n--- Teste de Memory Leak (Robust vs Bad) ---")
    
    # Cenário A: BadEventBus (Causa Leak)
    bad_bus = BadEventBus()
    temp_ui = UISystem("TempUI_Bad")
    bad_bus.subscribe(ScoreChangedEvent, temp_ui.on_score_changed)
    
    print("Deletando TempUI_Bad...")
    del temp_ui
    gc.collect() # Força coleta de lixo
    
    # Verificamos se o objeto ainda está no bus (via referência forte)
    # Em um sistema real, o objeto não sumiria da memória.
    # No BadEventBus, a lista ainda contém o método.
    leak_detected = len(bad_bus._subscribers[ScoreChangedEvent]) > 0
    print(f"[BAD_BUS] Leak detectado (objeto ainda vivo no bus): {leak_detected}")

    # Cenário B: RobustEventBus (Seguro)
    good_bus = RobustEventBus()
    temp_ui_good = UISystem("TempUI_Good")
    good_bus.subscribe(ScoreChangedEvent, temp_ui_good.on_score_changed)
    
    print("Deletando TempUI_Good...")
    del temp_ui_good
    gc.collect()
    
    # No RobustEventBus, a lista deve ser limpa ou a referência ser None
    leak_detected_good = len(good_bus._subscribers[ScoreChangedEvent]) > 0 and good_bus._subscribers[ScoreChangedEvent][0]() is not None
    print(f"[ROBUST_BUS] Leak detectado: {leak_detected_good}")
    
    assert not leak_detected_good, "RobustEventBus falhou em permitir a coleta do objeto!"
    print("\n[SUCESSO] Todos os critérios de missão atendidos.")

if __name__ == "__main__":
    test_performance_and_leaks()