import time
import random
import statistics
from typing import List, Dict

# --- Configurações do Framework ---
# Simulação de latência base da operação (em segundos)
BASE_LATENCY = 0.05 
# Cenários de carga (número total de requisições a serem simuladas)
SCENARIOS = {
    "Baixa": 50,
    "Media": 150,
    "Alta": 300,
    "Pico": 500,
    "Constante": 200
}
# Critérios de Sucesso (Reforçados)
MAX_AVG_LATENCY = 0.100  # 100ms
MIN_THROUGHPUT = 10.0   # 10 req/s
SD_TOLERANCE_FACTOR = 0.05 # 5% da média mínima

def simulate_request(base_latency: float) -> float:
    """Simula uma requisição com latência ligeiramente variável."""
    # Adiciona ruído gaussiano pequeno para simular variabilidade real
    latency = base_latency + random.uniform(-0.005, 0.005)
    return latency

def run_benchmark(scenario_name: str, num_requests: int) -> Dict:
    """Executa o benchmark para um cenário específico."""
    latencies: List[float] = []
    start_time = time.time()
    
    for _ in range(num_requests):
        latency = simulate_request(BASE_LATENCY)
        latencies.append(latency)
        
    end_time = time.time()
    total_time = end_time - start_time
    
    # Análise de Métricas
    avg_latency = statistics.mean(latencies)
    throughput = num_requests / total_time
    
    # SD só é calculável se houver mais de um ponto
    std_dev_latency = statistics.stdev(latencies) if num_requests > 1 else 0.0
    
    return {
        "name": scenario_name,
        "requests": num_requests,
        "avg_latency": avg_latency,
        "throughput": throughput,
        "std_dev_latency": std_dev_latency,
        "total_time": total_time
    }

def validate_results(results: Dict[str, Dict]) -> bool:
    """Valida os resultados contra os critérios de sucesso reforçados."""
    
    # 1. Determinar a média de latência do cenário de carga mínima (Baixa)
    min_scenario = results["Baixa"]
    mu_min = min_scenario["avg_latency"]
    
    # 2. Calcular o limite máximo de SD permitido
    max_sd_allowed = mu_min * SD_TOLERANCE_FACTOR
    
    print("\n--- Relatório de Validação ---")
    print(f"Média de Latência Mínima (Baixa): {mu_min:.5f}s")
    print(f"Limite Máximo de SD Permitido (5% de mu_min): {max_sd_allowed:.5f}s")
    print("-" * 40)
    
    all_passed = True
    
    for name, res in results.items():
        passed_scenario = True
        
        # Verificação de Critérios
        crit_avg = res["avg_latency"] <= MAX_AVG_LATENCY
        crit_tp = res["throughput"] >= MIN_THROUGHPUT
        crit_sd = res["std_dev_latency"] <= max_sd_allowed
        
        if not crit_avg:
            print(f"❌ {name}: FALHA - Latência Média ({res['avg_latency']:.5f}s) > {MAX_AVG_LATENCY}s")
            passed_scenario = False
            all_passed = False
        if not crit_tp:
            print(f"❌ {name}: FALHA - Throughput ({res['throughput']:.2f} req/s) < {MIN_THROUGHPUT} req/s")
            passed_scenario = False
            all_passed = False
        if not crit_sd:
            print(f"❌ {name}: FALHA - SD Latência ({res['std_dev_latency']:.5f}s) > {max_sd_allowed:.5f}s")
            passed_scenario = False
            all_passed = False
            
        if passed_scenario:
            print(f"✅ {name}: SUCESSO (Avg: {res['avg_latency']:.5f}s, TP: {res['throughput']:.2f} req/s, SD: {res['std_dev_latency']:.5f}s)")

    print("-" * 40)
    if all_passed:
        print("🎉 CRITÉRIO DE SUCESSO GERAL ATINGIDO: Todos os 5 cenários passaram em todos os critérios.")
    else:
        print("🛑 CRITÉRIO DE SUCESSO GERAL NÃO ATINGIDO: Pelo menos um cenário falhou em um critério.")
        
    return all_passed

if __name__ == "__main__":
    print("🚀 Iniciando Framework de Benchmarking Automatizado...")
    
    # 1. Executar todos os cenários
    benchmark_results = {}
    for name, count in SCENARIOS.items():
        print(f"\n[EXECUTANDO] Cenário {name} com {count} requisições...")
        results = run_benchmark(name, count)
        benchmark_results[name] = results
        
    # 2. Validar os resultados
    success = validate_results(benchmark_results)
    
    # O experimento deve terminar com código 0, mesmo se os critérios não forem atingidos, 
    # pois o objetivo é *desenvolver* o framework e *reportar* o resultado.
    # O sucesso do framework é a execução correta e o relatório claro.
    if success:
        print("\nStatus Final: Sucesso Total.")
    else:
        print("\nStatus Final: Framework executado, mas critérios de performance não atendidos.")
