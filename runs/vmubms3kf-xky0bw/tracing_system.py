import time
import uuid
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# --- 1. Estruturas de Dados do Trace ---

@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: float
    end_time: float = 0.0
    attributes: Dict[str, str] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000.0

# --- 2. Coletor Assíncrono com Ring Buffer (Alta Performance) ---

class AsyncSpanCollector:
    def __init__(self, buffer_size: int = 10000):
        self.buffer = queue.Queue(maxsize=buffer_size)
        self.active = True
        self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.worker_thread.start()
        self.collected_spans: List[Span] = []
        self._lock = threading.Lock()

    def submit(self, span: Span):
        try:
            self.buffer.put_nowait(span)
        except queue.Full:
            pass 

    def _process_loop(self):
        while self.active or not self.buffer.empty():
            try:
                span = self.buffer.get(timeout=0.1)
                with self._lock:
                    self.collected_spans.append(span)
                self.buffer.task_done()
            except queue.Empty:
                continue

    def shutdown(self):
        self.active = False
        self.worker_thread.join()

# --- 3. Propagação de Contexto W3C ---

class TraceContext:
    @staticmethod
    def inject(span: Span) -> Dict[str, str]:
        return {"traceparent": f"00-{span.trace_id}-{span.span_id}-01"}

    @staticmethod
    def extract(carrier: Dict[str, str]) -> Optional[Dict[str, str]]:
        traceparent = carrier.get("traceparent")
        if not traceparent:
            return None
        parts = traceparent.split("-")
        if len(parts) >= 3:
            return {"trace_id": parts[1], "parent_span_id": parts[2]}
        return None

# --- 4. Análise Corrigida de Caminho Crítico (BottleneckAnalyzer) ---

class BottleneckAnalyzer:
    @staticmethod
    def find_critical_path(spans: List[Span]) -> List[Span]:
        if not spans:
            return []

        # Mapeia spans por ID para acesso O(1)
        span_map = {s.span_id: s for s in spans}
        
        # Mapeia filhos por parent_span_id
        children_map: Dict[str, List[Span]] = {}
        roots: List[Span] = []
        
        for span in spans:
            if span.parent_span_id and span.parent_span_id in span_map:
                children_map.setdefault(span.parent_span_id, []).append(span)
            else:
                roots.append(span)

        if not roots:
            return []

        # Seleciona a raiz com maior duração
        current = max(roots, key=lambda s: s.duration_ms)
        critical_path = [current]

        # Navega recursivamente pelo filho que possui a maior duração (caminho crítico real)
        while current.span_id in children_map:
            children = children_map[current.span_id]
            if not children:
                break
            # O gargalo é o filho que consome mais tempo de execução
            next_span = max(children, key=lambda s: s.duration_ms)
            critical_path.append(next_span)
            current = next_span

        return critical_path

# --- 5. Experimento de Validação ---

def run_experiment():
    print("Iniciando experimento corrigido de Tracing Distribuído...")
    collector = AsyncSpanCollector()

    trace_id = uuid.uuid4().hex
    
    # Span 1: Gateway (Raiz)
    t_start = time.time()
    gateway_span = Span(
        trace_id=trace_id, 
        span_id=uuid.uuid4().hex[:16], 
        parent_span_id=None, 
        name="Gateway", 
        start_time=t_start
    )

    # Contexto propagado via W3C headers
    headers = TraceContext.inject(gateway_span)
    extracted_ctx = TraceContext.extract(headers)
    assert extracted_ctx is not None, "A extração do contexto W3C falhou."

    # Span 2: AuthService (Filho com maior latência - Gargalo Principal)
    t1 = time.time()
    time.sleep(0.025) # 25ms - Gargalo simulado
    auth_span = Span(
        trace_id=extracted_ctx["trace_id"], 
        span_id=uuid.uuid4().hex[:16], 
        parent_span_id=extracted_ctx["parent_span_id"], 
        name="AuthService", 
        start_time=t1, 
        end_time=time.time()
    )
    
    # Span 3: Database (Filho com menor latência)
    t2 = time.time()
    time.sleep(0.005) # 5ms
    db_span = Span(
        trace_id=trace_id, 
        span_id=uuid.uuid4().hex[:16], 
        parent_span_id=gateway_span.span_id, 
        name="Database", 
        start_time=t2, 
        end_time=time.time()
    )

    gateway_span.end_time = time.time()

    # Submetendo spans de forma assíncrona
    collector.submit(gateway_span)
    collector.submit(auth_span)
    collector.submit(db_span)

    # Aguardando processamento assíncrono
    time.sleep(0.2)
    collector.shutdown()

    # Validação e Análise
    print(f"Total de spans coletados assincronamente: {len(collector.collected_spans)}")
    
    critical_path = BottleneckAnalyzer.find_critical_path(collector.collected_spans)
    print("Caminho Crítico Identificado:")
    for span in critical_path:
        print(f" - [{span.name}] Duração: {span.duration_ms:.2f}ms")

    # Asserts rigorosos validados
    assert len(collector.collected_spans) == 3, "Deveria ter coletado exatamente 3 spans."
    assert len(critical_path) >= 2, "O caminho crítico deve conter pelo menos a raiz e o gargalo."
    assert critical_path[1].name == "AuthService", "O AuthService deveria ser identificado corretamente como o gargalo do caminho crítico."
    print("Experimento corrigido executado com sucesso e asserções validadas!")

if __name__ == "__main__":
    run_experiment()