path=main.py
import time
import random

class SystemUnderStress:
    def __init__(self, cpu_threshold=80.0):
        self.cpu_threshold = cpu_threshold
        self.current_cpu = 40.0
        self.cache = {"critical_data": "dados_em_cache_v1"}

    def simulate_load(self, traffic_intensity):
        # Saturação aumenta com a intensidade do tráfego
        self.current_cpu = min(100.0, 30.0 + (traffic_intensity * 1.5))

    def handle_request(self, request_type, is_critical):
        # 1. Verificação de Saturação para Load Shedding
        if self.current_cpu > self.cpu_threshold:
            if not is_critical:
                # Load Shedding ativado para tráfego não essencial
                return {
                    "status": 503,
                    "headers": {"Retry-After": "10"},
                    "body": "Service Temporarily Unavailable (Load Shedding Active)"
                }
        
        # 2. Graceful Degradation / Fallback para requisições críticas sob estresse
        if is_critical:
            if self.current_cpu > self.cpu_threshold:
                # Degradação funcional: serve do cache stale em vez de consultar BD pesado
                return {
                    "status": 200,
                    "headers": {"X-Fallback": "True", "Warning": "199 - Stale Response"},
                    "body": self.cache["critical_data"]
                }
            else:
                # Operação normal (lenta por simulação de BD)
                time.sleep(0.01)
                return {
                    "status": 200,
                    "headers": {"X-Fallback": "False"},
                    "body": "dados_frescos_do_db"
                }
        
        # Tráfego não essencial em condições normais
        time.sleep(0.005)
        return {"status": 200, "headers": {}, "body": "ok_nao_essencial"}

def run_experiment():
    print("Iniciando experimento de Load Shedding e Graceful Degradation...")
    sys = SystemUnderStress(cpu_threshold=75.0)

    # Cenário 1: Tráfego normal (CPU < 75%)
    sys.simulate_load(20) # CPU = 60%
    res_crit = sys.handle_request("GET /checkout", is_critical=True)
    res_nao = sys.handle_request("GET /recommendations", is_critical=False)
    
    print(f"[Normal] Crítico Status: {res_crit['status']}, Fallback: {res_crit['headers'].get('X-Fallback')}")
    print(f"[Normal] Não Essencial Status: {res_nao['status']}")
    assert res_crit["status"] == 200 and res_crit["headers"].get("X-Fallback") == "False"
    assert res_nao["status"] == 200

    # Cenário 2: Estresse Extremo (CPU > 75%)
    sys.simulate_load(60) # CPU = 120% -> Saturação!
    res_crit_stress = sys.handle_request("GET /checkout", is_critical=True)
    res_nao_stress = sys.handle_request("GET /recommendations", is_critical=False)

    print(f"[Estresse] Crítico Status: {res_crit_stress['status']}, Fallback: {res_crit_stress['headers'].get('X-Fallback')}")
    print(f"[Estresse] Não Essencial Status: {res_nao_stress['status']}, Retry-After: {res_nao_stress['headers'].get('Retry-After')}")
    
    # Validações de Critério de Sucesso
    assert res_nao_stress["status"] == 503, "Tráfego não essencial deve receber erro 503"
    assert "Retry-After" in res_nao_stress["headers"], "Resposta 503 deve conter Retry-After"
    assert res_crit_stress["status"] == 200, "Tráfego crítico deve ser preservado"
    assert res_crit_stress["headers"].get("X-Fallback") == "True", "Tráfego crítico deve usar degradação funcional (cache)"

    print("Experimento executado com sucesso e todas as asserções passaram!")

if __name__ == "__main__":
    run_experiment()