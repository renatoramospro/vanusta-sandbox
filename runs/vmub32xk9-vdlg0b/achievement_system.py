import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Set

# --- DOMÍNIO: EVENTOS (Imutáveis e com ID único) ---

@dataclass(frozen=True)
class GameEvent:
    event_id: str
    event_type: str
    payload: dict

# --- INFRAESTRUTURA: EVENT BUS (Desacoplamento) ---

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: GameEvent):
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                callback(event)

# --- DOMÍNIO: SISTEMA DE CONQUISTAS (Lógica e Persistência) ---

class AchievementSystem:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.processed_event_ids: Set[str] = set()  # Proteção contra duplicatas (Idempotência)
        self.audit_log: List[GameEvent] = []        # Auditoria (Event Sourcing)
        self.progress: Dict[str, int] = {}          # Estado atual (Cache)
        self.unlocked_achievements: Set[str] = set()

        # Subscreve aos eventos de interesse
        self.event_bus.subscribe("ENEMY_KILLED", self._on_enemy_killed)

    def _on_enemy_killed(self, event: GameEvent):
        # 1. Verificação de Idempotência (Evita processar o mesmo evento duas vezes)
        if event.event_id in self.processed_event_ids:
            print(f"[AchievementSystem] Ignorando evento duplicado: {event.event_id}")
            return

        # 2. Registro de Auditoria (Persistência Atômica do Evento)
        self.audit_log.append(event)
        self.processed_event_ids.add(event.event_id)

        # 3. Lógica de Regra de Negócio
        achievement_id = "SLAYER_10"
        current_count = self.progress.get(achievement_id, 0) + 1
        self.progress[achievement_id] = current_count

        print(f"[AchievementSystem] Evento processado. Progresso '{achievement_id}': {current_count}/10")

        if current_count >= 10 and achievement_id not in self.unlocked_achievements:
            self.unlocked_achievements.add(achievement_id)
            print(f"*** CONQUISTA DESBLOQUEADA: {achievement_id} ***")

# --- CORE GAMEPLAY (Totalmente desacoplado) ---

class GameEngine:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    def kill_enemy(self):
        # O jogo apenas emite um fato. Ele não sabe que existe um sistema de conquistas.
        event = GameEvent(
            event_id=str(uuid.uuid4()),
            event_type="ENEMY_KILLED",
            payload={"enemy_type": "goblin"}
        )
        print(f"[GameEngine] Inimigo morto. Emitindo evento {event.event_id}")
        self.event_bus.publish(event)

    def simulate_network_glitch_and_duplicate(self, original_event: GameEvent):
        # Simula um erro onde o mesmo evento é enviado novamente devido a uma retentativa de rede
        print(f"[GameEngine] SIMULANDO ERRO DE REDE: Reenviando evento {original_event.event_id}")
        self.event_bus.publish(original_event)

# --- TESTE DO EXPERIMENTO ---

def run_experiment():
    bus = EventBus()
    achievements = AchievementSystem(bus)
    game = GameEngine(bus)

    print("--- Início do Teste: Progresso Normal ---")
    for _ in range(3):
        game.kill_enemy()

    print("\n--- Teste de Idempotência (Evento Duplicado) ---")
    # Criamos um evento manual para simular a duplicata exata
    duplicate_event = GameEvent(
        event_id="fixed-id-123",
        event_type="ENEMY_KILLED",
        payload={"enemy_type": "goblin"}
    )
    bus.publish(duplicate_event) # Primeira vez
    bus.publish(duplicate_event) # Segunda vez (deve ser ignorada)

    print("\n--- Teste de Conclusão de Conquista ---")
    # Matar o restante para chegar em 10 (já temos 3 normais + 1 da duplicata que funcionou)
    for _ in range(6):
        game.kill_enemy()

    print("\n--- Verificação de Auditoria ---")
    print(f"Total de eventos no log de auditoria: {len(achievements.audit_log)}")
    print(f"Total de eventos processados (únicos): {len(achievements.processed_event_ids)}")
    
    # Validação final
    assert "SLAYER_10" in achievements.unlocked_achievements
    assert len(achievements.audit_log) == len(achievements.processed_event_ids)
    print("\n[RESULTADO] Experimento concluído com sucesso: Integridade e Desacoplamento validados.")

if __name__ == "__main__":
    run_experiment()