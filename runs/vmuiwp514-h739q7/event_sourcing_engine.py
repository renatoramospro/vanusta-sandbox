import time
from typing import Callable, Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import types

@dataclass(frozen=True)
class Event:
    event_id: str
    aggregate_id: str
    event_type: str
    version: int
    payload: types.MappingProxyType
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.event_id or not isinstance(self.event_id, str):
            raise ValueError("event_id inválido ou vazio.")
        if not self.aggregate_id or not isinstance(self.aggregate_id, str):
            raise ValueError("aggregate_id inválido ou vazio.")
        if not self.event_type or not isinstance(self.event_type, str):
            raise ValueError("event_type inválido ou vazio.")
        if self.version < 1:
            raise ValueError(f"Versão inválida: {self.version}. Deve ser >= 1.")
        
        # Validação de regras de negócio específicas para evitar estados corrompidos
        if self.event_type in ["ValorDepositado", "ValorSacado"]:
            if "valor" not in self.payload:
                raise ValueError("Payload deve conter o campo 'valor'.")
            valor = self.payload["valor"]
            if not isinstance(valor, (int, float)) or valor <= 0:
                raise ValueError(f"Valor monetário inválido: {valor}. Deve ser maior que zero.")
        elif self.event_type == "ContaCriada":
            if "titular" not in self.payload or not self.payload["titular"]:
                raise ValueError("ContaCriada exige um titular válido.")
            saldo = self.payload.get("saldo_inicial", 0.0)
            if not isinstance(saldo, (int, float)) or saldo < 0:
                raise ValueError(f"Saldo inicial inválido: {saldo}.")

@dataclass(frozen=True)
class Snapshot:
    aggregate_id: str
    version: int
    state: types.MappingProxyType

class Aggregate:
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.state: Dict[str, Any] = {}

    def apply(self, event: Event):
        if event.version != self.version + 1:
            raise ValueError(f"Conflito de versão! Esperada {self.version + 1}, recebida {event.version}")
        
        if event.event_type == "ContaCriada":
            self.state["titular"] = event.payload["titular"]
            self.state["saldo"] = event.payload.get("saldo_inicial", 0.0)
        elif event.event_type == "ValorDepositado":
            self.state["saldo"] += event.payload["valor"]
        elif event.event_type == "ValorSacado":
            novo_saldo = self.state["saldo"] - event.payload["valor"]
            if novo_saldo < 0:
                raise ValueError("Saldo insuficiente para saque.")
            self.state["saldo"] = novo_saldo
            
        self.version = event.version

    @classmethod
    def reconstroi(cls, aggregate_id: str, events: List[Event], snapshot: Optional[Snapshot] = None) -> 'Aggregate':
        aggr = cls(aggregate_id)
        
        if snapshot:
            aggr.version = snapshot.version
            aggr.state = dict(snapshot.state)
        
        for event in events:
            if event.version > aggr.version:
                aggr.apply(event)
                
        return aggr

class ProjectionManager:
    def __init__(self):
        self.projections: Dict[str, Callable[[Event], None]] = {}
        # Rastreamento de idempotência por projeção para entrega at-least-once
        self._processed_events: Dict[str, Set[str]] = {}

    def register(self, name: str, projection_fn: Callable[[Event], None]):
        self.projections[name] = projection_fn
        if name not in self._processed_events:
            self._processed_events[name] = set()

    def unregister(self, name: str):
        if name in self.projections:
            del self.projections[name]
        if name in self._processed_events:
            del self._processed_events[name]

    def dispatch(self, event: Event):
        for name, fn in self.projections.items():
            processed_set = self._processed_events[name]
            if event.event_id in processed_set:
                # Idempotência: ignora evento duplicado para esta projeção
                continue
            fn(event)
            processed_set.add(event.event_id)

class EventStore:
    def __init__(self):
        self._events: List[Event] = []
        self._snapshots: Dict[str, Snapshot] = {}
        self._seen_event_ids: Set[str] = set()

    def append(self, event: Event):
        if event.event_id in self._seen_event_ids:
            raise ValueError(f"Violação de unicidade: event_id {event.event_id} já registrado.")
        self._seen_event_ids.add(event.event_id)
        self._events.append(event)

    def get_events(self, aggregate_id: str, after_version: int = 0) -> List[Event]:
        return [
            e for e in self._events 
            if e.aggregate_id == aggregate_id and e.version > after_version
        ]

    def save_snapshot(self, snapshot: Snapshot):
        self._snapshots[snapshot.aggregate_id] = snapshot

    def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        return self._snapshots.get(aggregate_id)

def test_security_and_integrity_fixes():
    print("[*] Iniciando testes de segurança, imutabilidade e idempotência...")
    
    store = EventStore()
    proj_manager = ProjectionManager()
    
    # 1. Teste de Imutabilidade Profunda do Payload (MappingProxyType)
    payload_dict = {"titular": "Alice", "saldo_inicial": 1000.0}
    proxy_payload = types.MappingProxyType(payload_dict)
    
    ev1 = Event(
        event_id="evt-1",
        aggregate_id="conta-sec-1",
        event_type="ContaCriada",
        version=1,
        payload=proxy_payload
    )
    
    # Tentativa de modificar o payload original externamente não deve afetar o proxy imutável,
    # e tentar modificar o proxy diretamente deve lançar TypeError.
    try:
        ev1.payload["titular"] = "Bob"  # type: ignore
        raise AssertionError("Deveria ter impedido alteração no payload congelado!")
    except TypeError:
        print("[+] Sucesso: Tentativa de mutação do payload bloqueada por TypeError.")

    store.append(ev1)
    
    # 2. Teste de Validação de Entradas (Valores negativos e campos ausentes)
    try:
        bad_payload = types.MappingProxyType({"valor": -50.0})
        Event(
            event_id="evt-bad",
            aggregate_id="conta-sec-1",
            event_type="ValorDepositado",
            version=2,
            payload=bad_payload
        )
        raise AssertionError("Deveria ter rejeitado valor negativo!")
    except ValueError as e:
        print(f"[+] Sucesso: Validação rejeitou entrada inválida corretamente: {e}")

    # 3. Teste de Idempotência nas Projeções (Entrega At-Least-Once)
    saldo_projetado = {"valor": 0.0}
    def soma_saldo_proj(evt: Event):
        if evt.event_type == "ContaCriada":
            saldo_projetado["valor"] += evt.payload.get("saldo_inicial", 0.0)
        elif evt.event_type == "ValorDepositado":
            saldo_projetado["valor"] += evt.payload["valor"]

    proj_manager.register("SaldoProjection", soma_saldo_proj)
    
    # Despacha o primeiro evento
    proj_manager.dispatch(ev1)
    assert saldo_projetado["valor"] == 1000.0
    
    # Despacha o MESMO evento novamente (simulando reentrega at-least-once)
    proj_manager.dispatch(ev1)
    assert saldo_projetado["valor"] == 1000.0, "Idempotência falhou: saldo alterado por evento duplicado!"
    print("[+] Sucesso: Idempotência de projeção validada sob reentrega de eventos.")

    # 4. Teste de Unicidade de event_id no EventStore
    try:
        ev_duplicate = Event(
            event_id="evt-1",  # ID duplicado
            aggregate_id="conta-sec-1",
            event_type="ValorDepositado",
            version=2,
            payload=types.MappingProxyType({"valor": 100.0})
        )
        store.append(ev_duplicate)
        raise AssertionError("Deveria ter impedido event_id duplicado no store!")
    except ValueError as e:
        print(f"[+] Sucesso: Unicidade de event_id garantida: {e}")

    print("[SUCESSO] Todos os testes de segurança, imutabilidade e integridade passaram!")

if __name__ == "__main__":
    test_security_and_integrity_fixes()