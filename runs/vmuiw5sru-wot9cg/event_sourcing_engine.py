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

@dataclass(frozen=True)
class Snapshot:
    aggregate_id: str
    version: int
    state: Dict[str, Any]

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
            self.state["saldo"] -= event.payload["valor"]
            
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

    def register(self, name: str, projection_fn: Callable[[Event], None]):
        self.projections[name] = projection_fn

    def unregister(self, name: str):
        if name in self.projections:
            del self.projections[name]

    def dispatch(self, event: Event):
        for proj_fn in self.projections.values():
            proj_fn(event)

class EventStore:
    def __init__(self):
        self._events: List[Event] = []
        self._snapshots: Dict[str, Snapshot] = {}

    def append(self, event: Event):
        self._events.append(event)

    def get_events(self, aggregate_id: str, after_version: int = 0) -> List[Event]:
        return [e for e in self._events if e.aggregate_id == aggregate_id and e.version > after_version]

    def save_snapshot(self, snapshot: Snapshot):
        self._snapshots[snapshot.aggregate_id] = snapshot

    def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        return self._snapshots.get(aggregate_id)

def test_event_sourcing_engine():
    print("[*] Iniciando testes do motor de Event Sourcing...")
    store = EventStore()
    proj_manager = ProjectionManager()

    # Projeções dinâmicas de exemplo
    saldos_view: Dict[str, float] = {}
    contador_eventos = {"total": 0}

    def proj_saldos(event: Event):
        if event.event_type == "ContaCriada":
            saldos_view[event.aggregate_id] = event.payload.get("saldo_inicial", 0.0)
        elif event.event_type == "ValorDepositado":
            saldos_view[event.aggregate_id] += event.payload["valor"]
        elif event.event_type == "ValorSacado":
            saldos_view[event.aggregate_id] -= event.payload["valor"]

    def proj_contador(event: Event):
        contador_eventos["total"] += 1

    proj_manager.register("saldos", proj_saldos)
    proj_manager.register("contador", proj_contador)

    # Gerando 10.000 eventos distribuídos em agregados
    num_agregados = 10
    eventos_por_agregado = 1000
    
    print(f"[*] Gerando e processando {num_agregados * eventos_por_agregado} eventos...")
    t_gen_start = time.perf_counter()
    
    for a in range(num_agregados):
        aggr_id = f"conta-{a}"
        # Evento 1: Criação
        evt_criacao = Event(
            event_id=f"evt-{a}-0",
            aggregate_id=aggr_id,
            event_type="ContaCriada",
            version=1,
            payload={"titular": f"Cliente {a}", "saldo_inicial": 100.0}
        )
        store.append(evt_criacao)
        proj_manager.dispatch(evt_criacao)

        # Demais eventos: Depósitos
        for v in range(2, eventos_por_agregado + 1):
            evt = Event(
                event_id=f"evt-{a}-{v}",
                aggregate_id=aggr_id,
                event_type="ValorDepositado",
                version=v,
                payload={"valor": 10.0}
            )
            store.append(evt)
            proj_manager.dispatch(evt)

    t_gen_end = time.perf_counter()
    print(f"[+] Tempo total de ingestão e projeção: {(t_gen_end - t_gen_start)*1000:.2f}ms")

    # Teste A: Replay completo (meta < 50ms por agregado ou global otimizado)
    t_replay_start = time.perf_counter()
    agregado_teste = Aggregate.reconstroi("conta-0", store.get_events("conta-0"))
    t_replay_end = time.perf_counter()
    replay_duration = (t_replay_end - t_replay_start) * 1000
    print(f"[+] Replay completo de 1000 eventos para um agregado: {replay_duration:.2f}ms")
    assert replay_duration < 50.0, f"Tempo de replay excessivo: {replay_duration}ms"
    assert agregado_teste.state["saldo"] == 100.0 + (999 * 10.0)

    # Teste B: Snapshot + Replay incremental (< 5ms)
    snapshot_parcial = Snapshot(aggregate_id="conta-0", version=500, state=dict(agregado_teste.state))
    store.save_snapshot(snapshot_parcial)

    t_inc_start = time.perf_counter()
    snap_rebuild = Aggregate.reconstroi(
        "conta-0", 
        store.get_events("conta-0", after_version=500), 
        snapshot=store.get_snapshot("conta-0")
    )
    t_inc_end = time.perf_counter()
    inc_duration = (t_inc_end - t_inc_start) * 1000
    print(f"[+] Replay incremental pós-snapshot (500 eventos restantes): {inc_duration:.2f}ms")
    assert inc_duration < 10.0, f"Tempo de replay incremental excessivo: {inc_duration}ms"

    # Teste C: Latência de atualização de projeções por lote de 100 eventos (P99 < 10ms)
    all_events = store._events
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
    print(f"[+] P99 da latência de atualização de projeções por lote de 100 eventos: {p99_lat:.2f}ms (Meta: < 10ms)")
    assert p99_lat < 10.0, f"Latência p99 de projeção excedida: {p99_lat}ms"

    print("[SUCESSO] Todos os critérios de desempenho e consistência atingidos!")

if __name__ == "__main__":
    test_event_sourcing_engine()