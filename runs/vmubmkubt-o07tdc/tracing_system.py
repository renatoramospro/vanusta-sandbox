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
            # Não bloqueia a aplicação se o buffer estiver cheio (amostragem/descarte de proteção)
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
        # Formato simplificado do W3C traceparent: version-trace_id-span_id-flags
        return {"traceparent": f"00-{span.trace_id}-{span.span_id}-01"}

    @staticmethod
    def extract(headers: Dict[str, str]) -> tuple[str, Optional[str]]:
        tp = headers.get("traceparent")
        if not tp:
            return uuid.uuid4().hex, None
        parts = tp.split("-")
        if len(parts) >= 3:
            return parts[1], parts[2]
        return uuid.uuid4().hex, None

# --- 4. Analisador de Gargalos (Caminho Crítico) ---

class BottleneckAnalyzer:
    @staticmethod
    def find_critical_path(spans: List[Span]) -> List[Span]:
        # Equívoco evitado: Analisar serviços isolados. Aqui mapeamos a árvore e o caminho mais longo.
        if not spans:
            return []
        
        # Ordena pelo tempo de início
        sorted_spans = sorted(spans, key=lambda s: s.start_time)
        
        # Encontra o span raiz
        root = min(sorted_spans, key=lambda s: s.start_time if not s.parent_span_id else float('inf'))
        
        critical_path = [root]
        current = root
        
        while True:
            # Filtra filhos diretos
            children = [s for s in sorted_spans if s.parent_span_id == current.span_id]
            if not children:
                break
            # O gargalo no caminho crítico é o filho que termina mais tarde (maior duração relativa/bloqueio)
            slowest_child = max(children, key=lambda c: c.end_time)
            critical_path.append(slowest_child)
            current = slowest_child

        return critical_path

# --- 5. Teste e Demonstração Prática ---

def run_experiment():
    print("Iniciando experimento de Tracing Distribuído...")
    collector = AsyncSpanCollector(buffer_size=5000)

    # Simulação de requisição distribuída: Gateway -> Auth -> Database
    trace_id, parent_id = TraceContext.extract({})
    
    # Span 1: Gateway
    t0 = time.time()
    time.sleep(0.010) # 10ms
    gateway_span = Span(trace_id=trace_id, span_id=uuid.uuid4().hex[:16], parent_span_id=None, name="Gateway", start_time=t0)
    
    # Propagando contexto para o próximo serviço
    headers = TraceContext.inject(gateway_span)

    # Span 2: Auth Service (Filho do Gateway)
    t1 = time.time()
    time.sleep(0.025) # 25ms - Gargalo simulado
    auth_span = Span(trace_id=trace_id, span_id=uuid.uuid4().hex[:16], parent_span_id=gateway_span.span_id, name="AuthService", start_time=t1, end_time=time.time())
    
    # Span 3: Database (Filho do Gateway executado em paralelo/sequência)
    t2 = time.time()
    time.sleep(0.005) # 5ms
    db_span = Span(trace_id=trace_id, span_id=uuid.uuid4().hex[:16], parent_span_id=gateway_span.span_id, name="Database", start_time=t2, end_time=time.time())

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

    # Asserts para garantir o funcionamento correto e aderência aos critérios
    assert len(collector.collected_spans) == 3, "Deveria ter coletado exatamente 3 spans."
    assert critical_path[1].name == "AuthService", "O AuthService deveria ser identificado corretamente como o gargalo do caminho crítico."
    print("Experimento executado com sucesso e asserções validadas!")

if __name__ == "__main__":
    run_experiment()