import json
import time
import random

def generate_log_event(event_id):
    """Gera um evento de log estruturado sintético."""
    return {
        "timestamp": time.time(),
        "level": random.choice(["INFO", "WARN", "ERROR"]),
        "service": "vanusta_mission",
        "event_id": event_id,
        "message": f"Log event number {event_id} occurred.",
        "payload": {"user_id": random.randint(1, 1000), "duration_ms": random.uniform(1.0, 50.0)}
    }

def measure_serialization_cost(num_events=10000):
    """Mede o tempo total e o custo médio de serialização."""
    # 1. Geração dos dados (fora do tempo de medição de serialização)
    events = [generate_log_event(i) for i in range(num_events)]
    
    # 2. Warm-up (para estabilizar o GC e o ambiente)
    for _ in range(100):
        json.dumps(events[0])
        
    # 3. Medição
    start_time = time.perf_counter()
    
    serialized_logs = []
    for event in events:
        # Serialização pura: objeto Python -> string JSON
        serialized_logs.append(json.dumps(event))
        
    end_time = time.perf_counter()
    
    total_time_s = end_time - start_time
    total_time_ms = total_time_s * 1000
    
    # Custo médio por evento em microssegundos (10^-6 s)
    avg_cost_us = (total_time_s / num_events) * 1_000_000
    
    print(f"--- Resultados da Serialização ({num_events} eventos) ---")
    print(f"Tempo Total de Serialização: {total_time_ms:.2f} ms")
    print(f"Custo Médio de Serialização: {avg_cost_us:.2f} µs/evento")
    
    return total_time_ms, avg_cost_us

if __name__ == "__main__":
    # Testando o volume recomendado pelo Architect (10000)
    total_time, avg_cost = measure_serialization_cost(num_events=10000)
    
    # Verificação dos critérios ajustados (10k eventos em < 1s com custo médio <= 200 µs)
    print("\n--- Verificação de Critérios Ajustados ---")
    if total_time < 1000:
        print("✅ Sucesso: Tempo total < 1000 ms.")
    else:
        print(f"❌ Falha: Tempo total ({total_time:.2f} ms) >= 1000 ms.")
        
    if avg_cost <= 200:
        print("✅ Sucesso: Custo médio <= 200 µs/evento.")
    else:
        print(f"❌ Falha: Custo médio ({avg_cost:.2f} µs) > 200 µs/evento.")