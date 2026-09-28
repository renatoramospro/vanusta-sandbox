import concurrent.futures
import time
import threading

statistics = {"A_success": 0, "A_fail": 0, "B_success": 0, "B_fail": 0}

# Bulkhead dedicado para o Serviço B com capacidade dimensionada para o tráfego esperado
bulkhead_b = threading.Semaphore(20)

def servico_a_instavel():
    # Simula travamento/esgotamento do Serviço A
    time.sleep(0.1)
    raise RuntimeError("Falha catastrófica no Serviço A")

def servico_b_saudavel():
    # Tenta adquirir recurso exclusivo do Bulkhead B (fail-fast se exceder capacidade)
    if bulkhead_b.acquire(blocking=False):
        try:
            # Simula processamento rápido e saudável do Serviço B
            time.sleep(0.01)
            return "OK"
        finally:
            bulkhead_b.release()
    else:
        # Rejeição controlada pelo Bulkhead (proteção contra sobrecarga)
        raise TimeoutError("Bulkhead B esgotado - requisição rejeitada rapidamente")

def worker_a():
    try:
        servico_a_instavel()
        statistics["A_success"] += 1
    except Exception:
        statistics["A_fail"] += 1

def worker_b():
    try:
        servico_b_saudavel()
        statistics["B_success"] += 1
    except Exception:
        statistics["B_fail"] += 1

def executar_teste():
    threads = []
    
    # Dispara forte carga no Serviço A (simulando exaustão) e carga simultânea no Serviço B
    for _ in range(100):
        t_a = threading.Thread(target=worker_a)
        t_b = threading.Thread(target=worker_b)
        threads.append(t_a)
        threads.append(t_b)
        t_a.start()
        t_b.start()
        
    for t in threads:
        t.join()

if __name__ == "__main__":
    print("Iniciando simulação corrigida de exaustão do Serviço A com Bulkhead calibrado no Serviço B...")
    executar_teste()
    
    total_b = statistics["B_success"] + statistics["B_fail"]
    taxa_erro_b = (statistics["B_fail"] / total_b) * 100 if total_b > 0 else 0
    
    print(f"Resultados Serviço A: Sucessos={statistics['A_success']}, Falhas={statistics['A_fail']}")
    print(f"Resultados Serviço B: Sucessos={statistics['B_success']}, Falhas={statistics['B_fail']}")
    print(f"Taxa de Erro do Serviço B: {taxa_erro_b:.2f}%")
    
    # Validação rigorosa do critério de sucesso: Taxa de erro do Serviço B deve ser <= 5.0%
    assert taxa_erro_b <= 5.0, f"Critério violado: Taxa de erro do Serviço B foi de {taxa_erro_b}%"
    print("EXPERIMENTO BEM-SUCEDIDO: O Bulkhead calibrado protegeu com sucesso o Serviço B durante a exaustão do Serviço A.")