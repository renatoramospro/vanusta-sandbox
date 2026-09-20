import time
import uuid
from dataclasses import dataclass
from typing import List, Dict, Any

# --- 1. EVENTOS (Imutáveis) ---

@dataclass(frozen=True)
class Event:
    aggregate_id: str
    version: int

@dataclass(frozen=True)
class ContaCriada(Event):
    titular: str

@dataclass(frozen=True)
class ValorDepositado(Event):
    valor: float

@dataclass(frozen=True)
class ValorSacado(Event):
    valor: float

# --- 2. AGGREGATE ROOT (Escrita) ---

class ContaBancaria:
    def __init__(self):
        self.id = None
        self.titular = None
        self.saldo = 0.0
        self.version = 0
        self._uncommitted_events = []

    def apply(self, event: Event):
        """Aplica o evento ao estado interno (sem lógica de negócio)"""
        if isinstance(event, ContaCriada):
            self.id = event.aggregate_id
            self.titular = event.titular
            self.saldo = 0.0
        elif isinstance(event, ValorDepositado):
            self.saldo += event.valor
        elif isinstance(event, ValorSacado):
            self.saldo -= event.valor
        
        self.version = event.version

    def create(self, titular: str):
        event = ContaCriada(aggregate_id=str(uuid.uuid4()), version=1, titular=titular)
        self._apply_new_event(event)

    def depositar(self, valor: float):
        if valor <= 0:
            raise ValueError("Depósito deve ser positivo")
        event = ValorDepositado(aggregate_id=self.id, version=self.version + 1, valor=valor)
        self._apply_new_event(event)

    def sacar(self, valor: float):
        if valor > self.saldo:
            raise ValueError("Saldo insuficiente")
        event = ValorSacado(aggregate_id=self.id, version=self.version + 1, valor=valor)
        self._apply_new_event(event)

    def _apply_new_event(self, event: Event):
        self.apply(event)
        self._uncommitted_events.append(event)

    @classmethod
    def rebuild_from_history(cls, history: List[Event]) -> 'ContaBancaria':
        """Reconstrói o estado através do Replay"""
        aggregate = cls()
        for event in history:
            aggregate.apply(event)
        return aggregate

# --- 3. EVENT STORE & PROJEÇÃO (Leitura) ---

class EventStore:
    def __init__(self):
        self._storage: Dict[str, List[Event]] = {}

    def save(self, aggregate: ContaBancaria):
        if aggregate.id not in self._storage:
            self._storage[aggregate.id] = []
        
        for event in aggregate._uncommitted_events:
            self._storage[aggregate.id].append(event)
        aggregate._uncommitted_events = []

    def get_events(self, aggregate_id: str) -> List[Event]:
        return self._storage.get(aggregate_id, [])

class ContaProjecao:
    """Modelo de leitura otimizado (Read Model)"""
    def __init__(self):
        self.contas_resumo = {} # id -> {titular, saldo}

    def handle(self, event: Event):
        if isinstance(event, ContaCriada):
            self.contas_resumo[event.aggregate_id] = {"titular": event.titular, "saldo": 0.0}
        elif isinstance(event, ValorDepositado):
            self.contas_resumo[event.aggregate_id]["saldo"] += event.valor
        elif isinstance(event, ValorSacado):
            self.contas_resumo[event.aggregate_id]["saldo"] -= event.valor

# --- 4. TESTE E VALIDAÇÃO ---

def run_experiment():
    store = EventStore()
    projection = ContaProjecao()
    
    # A. Fluxo Normal
    conta = ContaBancaria()
    conta.create("Alice")
    conta.depositar(100.0)
    conta.sacar(30.0)
    
    # Salva no Store e atualiza Projeção (Simulando consistência eventual)
    store.save(conta)
    for e in store.get_events(conta.id):
        projection.handle(e)

    print(f"--- Teste de Consistência ---")
    print(f"Estado Aggregate: {conta.saldo} | Projeção: {projection.contas_resumo[conta.id]['saldo']}")
    assert conta.saldo == projection.contas_resumo[conta.id]['saldo'], "Inconsistência detectada!"
    print("✅ Consistência validada.\n")

    # B. Teste de Performance e Replay (1000 eventos)
    print(f"--- Teste de Performance (Replay 1000 eventos) ---")
    conta_bulk = ContaBancaria()
    conta_bulk.create("Bob")
    for i in range(1, 1001):
        conta_bulk.depositar(10.0)
    
    store.save(conta_bulk)
    bulk_id = conta_bulk.id
    history = store.get_events(bulk_id)
    
    start_time = time.perf_counter()
    reconstructed_conta = ContaBancaria.rebuild_from_history(history)
    end_time = time.perf_counter()
    
    duration_ms = (end_time - start_time) * 1000
    print(f"Tempo de Replay: {duration_ms:.4f}ms")
    print(f"Saldo Reconstruído: {reconstructed_conta.saldo}")
    
    # Validações do critério de sucesso
    assert duration_ms < 200, f"Performance falhou: {duration_ms}ms"
    assert reconstructed_conta.saldo == 10000.0, "Saldo incorreto no replay"
    print("✅ Performance e Integridade do Replay validadas.")

    # C. Contraexemplo: Tentativa de estado inválido (Regra de Negócio)
    print(f"\n--- Teste de Regra de Negócio (Contraexemplo) ---")
    try:
        conta_errada = ContaBancaria()
        conta_errada.create("Charlie")
        conta_errada.sacar(500.0) # Saldo é 0
    except ValueError as e:
        print(f"✅ Capturado erro esperado: {e}")
    else:
        raise AssertionError("O sistema permitiu um saque sem saldo!")

if __name__ == "__main__":
    run_experiment()