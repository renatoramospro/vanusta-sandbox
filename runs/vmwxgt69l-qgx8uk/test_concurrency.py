import threading
import time

# Simulação do Store NoSQL
DATA_STORE = {"counter": 0}
# Simulação de um mecanismo de controle de concorrência (Locking Pessimista simples)
LOCK = threading.Lock()

def transaction_worker(thread_id):
    """Simula uma transação que lê, calcula e escreve."""
    global DATA_STORE
    
    # Tenta adquirir o lock para garantir isolamento
    with LOCK:
        # 1. Leitura
        current_value = DATA_STORE["counter"]
        
        # Simulação de latência de processamento (onde a concorrência ocorre)
        time.sleep(0.01) 
        
        # 2. Cálculo
        new_value = current_value + 1
        
        # 3. Escrita (Atomicidade garantida pelo lock)
        DATA_STORE["counter"] = new_value
        print(f"Thread {thread_id}: Atualizado para {new_value}")

# --- Teste de Concorrência ---
NUM_THREADS = 100
threads = []

# Resetar o estado inicial
DATA_STORE["counter"] = 0

print("--- Iniciando Teste de Concorrência com Locking ---")
start_time = time.time()

for i in range(NUM_THREADS):
    t = threading.Thread(target=transaction_worker, args=(i,))
    threads.append(t)
    t.start()

# Esperar todas as threads terminarem
for t in threads:
    t.join()

end_time = time.time()

final_value = DATA_STORE["counter"]
expected_value = NUM_THREADS

print("\n--- Resultados do Teste ---")
print(f"Valor Final Esperado: {expected_value}")
print(f"Valor Final Observado: {final_value}")
print(f"Tempo total: {end_time - start_time:.4f}s")

# Verificação de sucesso (Atomicidade e Isolamento garantidos pelo Lock)
assert final_value == expected_value, "FALHA: A concorrência resultou em perda de atualização (Lost Update)."
print("SUCESSO: Atomicidade e Isolamento garantidos. O valor final corresponde ao número de transações.")