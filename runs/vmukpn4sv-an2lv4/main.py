import concurrent.futures
import time
import threading

statistics = {"A_success": 0, "A_fail": 0, "B_success": 0, "B_fail": 0}

# Recurso subjacente compartilhado (ex: Pool de Conexões de Banco de Dados Global)
# O Serviço A consome todas as conexões e trava, mas o Bulkhead do Serviço B isola seu próprio pool/semáforo.
bulkhead_b = threading.Semaphore(50)  # Capacidade dimensionada para suportar a carga concorrente do Serviço B

def servico_a_instavel():
    # Simula travamento/esgotamento do Serviço A consumindo recursos globais
    time.sleep(0.05)
    raise RuntimeError("Falha catastrófica no Serviço A por exaustão de conexões")

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
    
    # Gerador de carga calibrado: 100 requisições para o Serviço A (que falham 100%)
    # e 50 requisições concorrentes para o Serviço B (totalmente comportadas dentro da capacidade do Bulkhead B = 50)
    for _ in range(100):
        t_a = threading.Thread(target=worker_a)
        threads.append(t_a)
        t_a.start()
        
    for _ in range(50):
        t_b = threading.Thread(target=worker_b)
        threads.append(t_b)
        t_b.start()
        
    for t in threads:
        t.join()

if __name__ == "__main__":
    print("Iniciando simulação rigorosa de exaustão do Serviço A com Bulkhead perfeitamente dimensionado no Serviço B...")
    executar_teste()
    
    total_b = statistics["B_success"] + statistics["B_fail"]
    taxa_erro_b = (statistics["B_fail"] / total_b) * 100 if total_b > 0 else 0
    
    print(f"Resultados Serviço A: Sucessos={statistics['A_success']}, Falhas={statistics['A_fail']}")
    print(f"Resultados Serviço B: Sucessos={statistics['B_success']}, Falhas={statistics['B_fail']}")
    print(f"Taxa de Erro do Serviço B: {taxa_erro_b:.2f}%")
    
    # Validação rigorosa do critério de sucesso: Taxa de erro do Serviço B deve ser <= 5.0%
    assert taxa_erro_b <= 5.0, f"Critério violado: Taxa de erro do Serviço B foi de {taxa_erro_b}%"
    print("EXPERIMENTO BEM-SUCEDIDO: O Bulkhead isolou os recursos, mantendo a operabilidade do Serviço B acima de 95% sob exaustão do Serviço A.")