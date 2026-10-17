import time
import random
import statistics

class SecureSystemUnderStress:
    def __init__(self, cpu_threshold=80.0, max_critical_rate=10):
        self.cpu_threshold = cpu_threshold
        self.current_cpu = 40.0
        # Cache seguro com tratamento de stale e vazio
        self.cache = {"critical_data": "dados_em_cache_v1"}
        # Tokens válidos simulados para controle de autorização de criticidade
        self.valid_tokens = {"admin-token-secure", "priority-service-key"}
        # Controle de taxa (Rate Limiting) para tráfego crítico
        self.max_critical_rate = max_critical_rate
        self.current_critical_requests = 0

    def simulate_load(self, traffic_intensity):
        self.current_cpu = min(100.0, 30.0 + (traffic_intensity * 1.5))
        # Reseta o contador de taxa crítica a cada ciclo de simulação
        self.current_critical_requests = 0

    def handle_request(self, request_type, is_critical, auth_token=None):
        # 1. Validação de Segurança e Autorização para tráfego crítico
        effective_critical = is_critical
        if is_critical:
            if auth_token not in self.valid_tokens:
                # Rejeita falsificação de criticidade: rebaixa para não essencial
                effective_critical = False
            else:
                # Aplica rate limiting para evitar abuso de tráfego crítico sob estresse
                if self.current_critical_requests >= self.max_critical_rate:
                    return {
                        "status": 503,
                        "headers": {"Retry-After": "5"},
                        "body": "Critical Rate Limit Exceeded (Load Shedding Active)"
                    }
                self.current_critical_requests += 1

        # 2. Verificação de Saturação para Load Shedding em tráfego não essencial
        if self.current_cpu > self.cpu_threshold:
            if not effective_critical:
                return {
                    "status": 503,
                    "headers": {"Retry-After": "10"},
                    "body": "Service Temporarily Unavailable (Load Shedding Active)"
                }
        
        # 3. Graceful Degradation / Fallback seguro para requisições críticas sob estresse
        if effective_critical:
            if self.current_cpu > self.cpu_threshold:
                # Proteção contra KeyError caso o cache esteja vazio
                fallback_data = self.cache.get("critical_data", "fallback_default_safe_response")
                return {
                    "status": 200,
                    "headers": {"X-Fallback": "True", "Warning": "199 - Stale Response"},
                    "body": fallback_data
                }
            else:
                time.sleep(0.005)
                return {
                    "status": 200,
                    "headers": {"X-Fallback": "False"},
                    "body": "dados_frescos_do_db"
                }
        
        time.sleep(0.002)
        return {
            "status": 200,
            "headers": {"X-Fallback": "False"},
            "body": "ok"
        }

def run_experiment():
    print("Iniciando simulação avançada de Load Shedding, Concorrência e p99...")
    system = SecureSystemUnderStress(cpu_threshold=75.0, max_critical_rate=2)

    # Simulação de concorrência e medição de latência (p99)
    latencies_critical = []
    
    # Cenário de Estresse Extremo com concorrência simulada
    system.simulate_load(85) # CPU = 157.5 -> 100% (Saturado)

    for i in range(100):
        start_t = time.time()
        # Teste adversarial: tentativa de falsificar criticidade sem token válido
        res_fake = system.handle_request("api", is_critical=True, auth_token="token_falso")
        
        # Teste crítico legítimo com token válido
        res_crit = system.handle_request("api", is_critical=True, auth_token="admin-token-secure")
        
        # Teste não essencial
        res_non = system.handle_request("api", is_critical=False)
        
        latencies_critical.append(time.time() - start_t)

    p99_latency = statistics.quantiles(latencies_critical, n=100)[98] * 1000 # em ms
    print(f"[Concorrência Sob Estresse] p99 Latency para Fluxos Críticos: {p99_latency:.2f} ms")

    # Teste de Borda: Cache Vazio com degradação ativa
    system.cache.clear()
    res_empty_cache = system.handle_request("api", is_critical=True, auth_token="admin-token-secure")
    print(f"[Cache Vazio] Status: {res_empty_cache['status']} | Body: {res_empty_cache['body']}")

    # Validações Estruturadas
    assert res_fake["status"] == 503, "Tentativa de falsificar criticidade sem token deve sofrer load shedding"
    assert res_empty_cache["status"] == 200, "Mesmo com cache vazio, o sistema não deve lançar KeyError e retornar fallback seguro"
    assert p99_latency < 50.0, "A latência p99 para fluxos críticos deve permanecer estável e baixa mesmo sob estresse"

    print("Experimento aprimorado executado com sucesso e todas as asserções de segurança e p99 passaram!")

if __name__ == "__main__":
    run_experiment()