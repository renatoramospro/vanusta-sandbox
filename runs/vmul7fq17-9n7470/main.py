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
        return {
            "status": 200,
            "headers": {"X-Fallback": "False"},
            "body": "ok"
        }

def run_experiment():
    print("Iniciando simulação de Load Shedding e Graceful Degradation...")
    system = SystemUnderStress(cpu_threshold=75.0)

    # Cenário 1: Tráfego normal
    system.simulate_load(20) # CPU = 60% (abaixo do threshold)
    res_normal_crit = system.handle_request("api", is_critical=True)
    res_normal_non = system.handle_request("api", is_critical=False)
    
    print(f"[Normal] Crítico Status: {res_normal_crit['status']} | Fallback: {res_normal_crit['headers'].get('X-Fallback')}")
    print(f"[Normal] Não-Crítico Status: {res_normal_non['status']}")

    # Cenário 2: Tráfego extremo / Saturação
    system.simulate_load(70) # CPU = 135% -> Clampeado em 100% (acima do threshold de 75%)
    res_stress_non = system.handle_request("api", is_critical=False)
    res_stress_crit = system.handle_request("api", is_critical=True)

    print(f"[Estresse] Não-Crítico (Load Shedding) Status: {res_stress_non['status']} | Retry-After: {res_stress_non['headers'].get('Retry-After')}")
    print(f"[Estresse] Crítico (Degradação) Status: {res_stress_crit['status']} | Fallback: {res_stress_crit['headers'].get('X-Fallback')}")

    # Validações estruturadas para garantir o critério de sucesso
    assert res_stress_non["status"] == 503, "Tráfego não essencial sob estresse deve receber erro 503"
    assert "Retry-After" in res_stress_non["headers"], "Resposta 503 deve conter o cabeçalho Retry-After"
    assert res_stress_crit["status"] == 200, "Tráfego crítico deve ser preservado mesmo sob estresse"
    assert res_stress_crit["headers"].get("X-Fallback") == "True", "Tráfego crítico sob estresse deve acionar degradação funcional (cache stale)"

    print("Experimento executado com sucesso e todas as asserções passaram!")

if __name__ == "__main__":
    run_experiment()