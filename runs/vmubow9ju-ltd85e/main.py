import json
import time
from datetime import datetime, timezone

class LogEvent:
    def __init__(self, service: str, level: str, message: str, trace_id: str, metadata: dict = None):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.service = service
        self.level = level
        self.message = message
        self.trace_id = trace_id
        self.metadata = metadata or {}

    def to_json(self) -> str:
        return json.dumps({
            "timestamp": self.timestamp,
            "service": self.service,
            "level": self.level,
            "message": self.message,
            "trace_id": self.trace_id,
            "metadata": self.metadata
        })

class LogIngestionPipeline:
    def __init__(self):
        self.buffer = []

    def ingest(self, log_json: str):
        event = json.loads(log_json)
        self.buffer.append(event)

    def process_stream(self):
        # Simula processamento em tempo real (< 5 segundos)
        start_time = time.time()
        error_count = 0
        total_events = len(self.buffer)
        
        for event in self.buffer:
            if event["level"] == "ERROR":
                error_count += 1
                
        duration = time.time() - start_time
        return {
            "total_events": total_events,
            "error_count": error_count,
            "processing_time_ms": duration * 1000
        }

class DynamicThresholdAnomalyDetector:
    def __init__(self, window_size: int = 5, threshold_multiplier: float = 2.0):
        self.window_size = window_size
        self.threshold_multiplier = threshold_multiplier
        self.history = []

    def evaluate(self, current_error_rate: float) -> bool:
        self.history.append(current_error_rate)
        if len(self.history) > self.window_size:
            self.history.pop(0)
            
        if len(self.history) < self.window_size:
            return False # Dados insuficientes para média móvel
            
        mean = sum(self.history[:-1]) / (len(self.history) - 1) if len(self.history) > 1 else self.history[0]
        # Limiar dinâmico baseado na média móvel + multiplicador de desvio/sensibilidade
        threshold = mean * self.threshold_multiplier
        
        # Anomalia detectada se a taxa atual ultrapassar o limiar dinâmico
        return current_error_rate > threshold and current_error_rate > 5 # Mínimo absoluto para evitar ruído

def demonstrate_structured_vs_unstructured():
    print("--- Demonstração 1: Log Estruturado vs Texto Plano ---")
    # Contraexemplo do equívoco comum: Logs em texto plano exigem Regex frágil e custosa
    unstructured_log = "2023-10-25 10:00:00 [ERROR] auth-service - Failed to authenticate user [TraceID: abc-123]"
    print(f"Texto Plano (Frágil): {unstructured_log}")
    
    # Abordagem correta: Log Estruturado em JSON
    structured_log = LogEvent(
        service="auth-service",
        level="ERROR",
        message="Failed to authenticate user",
        trace_id="abc-123",
        metadata={"user_id": 42, "ip": "192.168.1.10"}
    )
    json_output = structured_log.to_json()
    print(f"Estruturado (Robusto/Parse Direto): {json_output}")
    parsed = json.loads(json_output)
    assert parsed["level"] == "ERROR"
    print("-> Sucesso: Parse de log estruturado validado sem uso de Regex.\n")

def demonstrate_dynamic_vs_static_alerts():
    print("--- Demonstração 2: Alertas Dinâmicos vs Limiar Estático ---")
    detector = DynamicThresholdAnomalyDetector(window_size=3, threshold_multiplier=1.5)
    
    # Simulação de tráfego normal com variação natural
    traffic = [2, 3, 2, 15] # O último valor é um pico de erros
    
    anomalies = []
    for i, errors in enumerate(traffic):
        is_anomaly = detector.evaluate(errors)
        anomalies.append((errors, is_anomaly))
        print(f"Janela Passo {i+1} - Erros: {errors} | Anomalia Detectada?: {is_anomaly}")

    # Validação do contraexemplo: Limiar estático fixo em 10 geraria falso positivo se o tráfego normal subisse para 11,
    # ou falharia se o pico estivesse abaixo de 10 num horário de baixo movimento.
    # O limiar dinâmico adaptou-se ao histórico recente.
    assert anomalies[-1][1] == True, "O pico de erros deveria ser detectado como anomalia."
    print("-> Sucesso: Detecção de anomalia por limiar dinâmico validada com sucesso.\n")

def demonstrate_pipeline_performance():
    print("--- Demonstração 3: Performance de Coleta e Ingestão ---")
    pipeline = LogIngestionPipeline()
    
    # Simula lote de eventos (escala para teste de throughput)
    event_count = 1000
    start_gen = time.time()
    for i in range(event_count):
        level = "ERROR" if i % 10 == 0 else "INFO"
        log = LogEvent("payment-service", level, f"Transaction {i}", f"tr-{i}")
        pipeline.ingest(log.to_json())
    gen_duration = time.time() - start_gen
    
    metrics = pipeline.process_stream()
    print(f"Total de eventos injetados: {metrics['total_events']}")
    print(f"Erros detectados: {metrics['error_count']}")
    print(f"Tempo de processamento da stream: {metrics['processing_time_ms']:.2f} ms")
    
    # Critério de sucesso parcial: processar e exibir métricas em menos de 5 segundos (< 5000ms)
    assert metrics['processing_time_ms'] < 5000, "O processamento excedeu o limite de 5 segundos!"
    print(f"-> Sucesso: Processamento de {event_count} eventos concluídos em {metrics['processing_time_ms']:.2f}ms (bem abaixo do limite de 5s).")

if __name__ == "__main__":
    demonstrate_structured_vs_unstructured()
    demonstrate_dynamic_vs_static_alerts()
    demonstrate_pipeline_performance()
    print("\nTodos os experimentos executados e validados com código de saída 0.")