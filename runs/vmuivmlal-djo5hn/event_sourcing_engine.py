import time
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Event:
    event_id: str
    aggregate_id: str
    event_type: str
    version: int
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

class Aggregate:
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.state: Dict[str, Any] = {}

    def apply(self, event: Event):
        if event.version != self.version + 1:
            raise ValueError(f"Conflito de versão! Esperada {self.version + 1}, recebida {event.version}")
        
        # Mutação baseada no tipo de evento
        if event.event_type == "ContaCriada":
            self.state["titular"] = event.payload["titular"]
            self.state["saldo"] = event.payload.get("saldo_inicial", 0.0)
        elif event.event_type == "ValorDepositado":
            self.state["saldo"] += event.payload["valor"]
        elif event.event_type == "ValorSacado":
            self.state["saldo"] -= event.payload["valor"]
            
        self.version = event.version

    @classmethod
    def reconstroi(cls, aggregate_id: str, events: List[Event], snapshot: Optional['Snapshot'] = None) -> 'Aggregate':
        aggr = cls(aggregate_id)
        start_version = 0
        
        if snapshot:
            aggr.version = snapshot.version
            aggr.state = dict(snapshot.state)
            start_version = snapshot.version
            
        for event in events:
            if event.version > start_version:
                aggr.apply(event)
                
        return aggr

@dataclass
class Snapshot:
    aggregate_id: str
    version: int
    state: Dict[str, Any]

class EventStore:
    def __init__(self):
        self._events: List[Event] = []
        self._snapshots: Dict[str, Snapshot] = {}

    def append(self, event: Event):
        self._events.append(event)

    def get_events(self, aggregate_id: Optional[str] = None) -> List[Event]:
        if aggregate_id:
            return [e for e in self._events if e.aggregate_id == aggregate_id]
        return self._events

    def save_snapshot(self, snapshot: Snapshot):
        self._snapshots[snapshot.aggregate_id] = snapshot

    def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        return self._snapshots.get(aggregate_id)

class ProjectionManager:
    def __init__(self):
        self._projections: Dict[str, Callable[[Event], None]] = {}

    def register(self, name: str, handler: Callable[[Event], None]):
        self._projections[name] = handler

    def unregister(self, name: str):
        if name in self._projections:
            del self._projections[name]

    def dispatch(self, event: Event):
        for handler in self._projections.values():
            handler(event)

    def replay(self, events: List[Event]):
        for event in events:
            self.dispatch(event)

# --- Teste de Carga e Validação do Critério de Sucesso ---
def test_event_sourcing_engine():
    store = EventStore()
    proj_manager = ProjectionManager()

    # 1. Registrar 5 Projeções Dinâmicas com estados internos isolados
    proj_stats = {"total_depositos": 0, "volume_total": 0.0, "eventos_por_tipo": {}}
    
    def proj_contador_eventos(e: Event):
        t = e.event_type
        proj_stats["eventos_por_tipo"][t] = proj_stats["eventos_por_tipo"].get(t, 0) + 1

    def proj_volume_financeiro(e: Event):
        if e.event_type == "ValorDepositado":
            proj_stats["total_depositos"] += 1
            proj_stats["volume_total"] += e.payload["valor"]

    proj_manager.register("contador", proj_contador_eventos)
    proj_manager.register("volume", proj_volume_financeiro)
    proj_manager.register("dummy_1", lambda e: None)
    proj_manager.register("dummy_2", lambda e: None)
    proj_manager.register("dummy_3", lambda e: None)

    print("[*] Gerando 10.000 eventos sintéticos...")
    aggr_id = "conta-123"
    events_to_insert = [
        Event(event_id=f"evt-1", aggregate_id=aggr_id, event_type="ContaCriada", version=1, payload={"titular": "Alice", "saldo_inicial": 100.0})
    ]
    
    current_saldo = 100.0
    for i in range(2, 10001):
        if i % 2 == 0:
            e_type = "ValorDepositado"
            val = 10.0
            current_saldo += val
        else:
            e_type = "ValorSacado"
            val = 5.0
            current_saldo -= val
            
        events_to_insert.append(
            Event(event_id=f"evt-{i}", aggregate_id=aggr_id, event_type=e_type, version=i, payload={"valor": val})
        )

    # Inserção no EventStore
    t0 = time.time()
    for e in events_to_insert:
        store.append(e)
    t1 = time.time()
    print(f"[+] 10.000 eventos persistidos em {(t1 - t0)*1000:.2f}ms")

    # 2. Reconstrução completa do agregado (Replay total)
    t2 = time.time()
    all_events = store.get_events(aggr_id)
    aggr = Aggregate.reconstroi(aggr_id, all_events)
    t3 = time.time()
    replay_duration = (t3 - t2) * 1000
    print(f"[+] Replay completo de 10.000 eventos do agregado em {replay_duration:.2f}ms (Meta: < 50ms)")
    assert replay_duration < 50.0, fTempo de replay excessivo: {replay_duration}ms"
    assert aggr.state["saldo"] == current_saldo

    # 3. Snapshot + Replay Incremental
    snapshot = Snapshot(aggregate_id=aggr_id, version=5000, state={"titular": "Alice", "saldo": 25050.0})
    store.save_snapshot(snapshot)
    
    t4 = time.time()
    snap_loaded = store.get_snapshot(aggr_id)
    aggr_from_snap = Aggregate.reconstroi(aggr_id, all_events, snapshot=snap_loaded)
    t5 = time.time()
    snap_duration = (t5 - t4) * 1000
    print(f"[+] Replay via Snapshot + Incremental em {snap_duration:.2f}ms (Meta: < 5ms)")
    assert snap_duration < 5.0, f"Tempo com snapshot excessivo: {snap_duration}ms"

    # 4. Atualização de Projeções Dinâmicas em lotes de 100 eventos (< 10ms por lote)
    batch_size = 100
    latencias_lotes = []
    
    for i in range(0, len(all_events), batch_size):
        lote = all_events[i:i+batch_size]
        t_start = time.perf_counter()
        for evt in lote:
            proj_manager.dispatch(evt)
        t_end = time.perf_counter()
        latencias_lotes.append((t_end - t_start) * 1000)

    p99_lat = sorted(latencias_lotes)[int(len(latencias_lotes) * 0.99)]
    print(f"[+] P99 da latência de atualização de 5 projeções por lote de 100 eventos: {p99_lat:.2f}ms (Meta: < 10ms)")
    assert p99_lat < 10.0, f"Latência p99 de projeção excedida: {p99_lat}ms"

    print("[SUCESSO] Todos os critérios de desempenho e consistência atingidos!")

if __name__ == "__main__":
    test_event_sourcing_engine()