import concurrent.futures
import time
import threading
statistics = {"A_success": 0, "A_fail": 0, "B_success": 0, "B_fail": 0}

# Semáforo simulando o Bulkhead para o Serviço B (isolando recursos)
bulkhead_b = threading.Semaphore(5)

def servico_a_instavel():
    # Simula travamento/esgotamento
    time.sleep(0.5)
    raise RuntimeError("Serviço A esgotado!")

def servico_b_protegido():
    # Tenta adquirir recurso exclusivo no bulkhead com timeout rápido (fail-fast)
    if bulkhead_b.acquire(blocking=True, timeout=0.05):
        try:
            # Simula processamento rápido e saudável do Serviço B
            time.sleep(0.01)
            return "OK_B"
        finally:
            bulkhead_b.release()
    else:
        raise TimeoutError("Bulkhead B rejeitou requisição por saturação")

def worker(tipo):
    if tipo == 'A':
        try:
            servico_a_instavel()
            statistics["A_success"] += 1
        except Exception:
            statistics["A_fail"] += 1
    else:
        start = time.time()
        try:
            res = servico_b_protegido()
            duration = time.time() - start
            if duration <= 0.2:
                statistics["B_success"] += 1
            else:
                statistics["B_fail"] += 1
        except Exception:
            statistics["B_fail"] += 1

def executar_teste():
    threads = []
    # Saturar o sistema com muitas requisições simultâneas para A e B
    for _ in range(50):
        t = threading.Thread(target=worker, args=('A',))
        threads.append(t)
        t.start()
        
    for _ in range(50):
        t = threading.Thread(target=worker, args=('B',))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    print("Iniciando simulação de exaustão do Serviço A com Bulkhead no Serviço B...")
    executar_teste()
    
    total_b = statistics["B_success"] + statistics["B_fail"]
    taxa_erro_b = (statistics["B_fail"] / total_b) * 100 if total_b > 0 else 0
    
    print(f"Resultados Serviço A: Sucessos={statistics['A_success']}, Falhas={statistics['A_fail']}")
    print(f"Resultados Serviço B: Sucessos={statistics['B_success']}, Falhas={statistics['B_fail']}")
    print(f"Taxa de Erro do Serviço B: {taxa_erro_b:.2f}%")
    
    # Validação do critério de sucesso: Serviço B deve manter operabilidade >= 80% (erro <= 20%, idealmente <= 5%)
    assert taxa_erro_b <= 5.0, f"Critério violado: Taxa de erro do Serviço B foi de {taxa_erro_b}%"
    print("EXPERIMENTO BEM-SUCEDIDO: O Bulkhead protegeu com sucesso o Serviço B durante a falha do Serviço A.")