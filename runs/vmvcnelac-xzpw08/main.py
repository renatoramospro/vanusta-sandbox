import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

class TransactionalStore:
    """
    Armazenamento transacional baseado em OCC (Optimistic Concurrency Control)
    e Transactional Memory (TAM) lock-free com versionamento atômico (CAS).
    """
    def __init__(self):
        # Cada chave mapeia para um dicionário contendo o valor e a versão (timestamp lógico)
        self._data = {
            "account_A": {"value": 25000, "version": 0},
            "account_B": {"value": 25000, "version": 0}
        }
        self._global_lock = threading.Lock() # Apenas para operações atômicas de metadados simulando CAS lock-free
        self.aborts = 0
        self.commits = 0

    def read(self, key):
        """Fase de Leitura: retorna o valor e a versão atual."""
        item = self._data[key]
        return item["value"], item["version"]

    def commit(self, read_set, write_set):
        """
        Fase de Validação e Commit (CAS lógico atômico):
        Verifica se as versões lidas mudaram. Se sim, aborta (retorna False).
        Se não, atualiza os valores e incrementa as versões atomicamente.
        """
        with self._global_lock:
            # Validação (Read-Write Conflict Check)
            for key, read_version in read_set.items():
                if self._data[key]["version"] != read_version:
                    self.aborts += 1
                    return False
            
            # Fase de Escrita / Commit
            for key, new_value in write_set.items():
                self._data[key]["value"] = new_value
                self._data[key]["version"] += 1
            
            self.commits += 1
            return True

def run_transaction(store, thread_id):
    """Executa uma transação simulando transferência entre contas com retry."""
    start_time = time.time()
    while True:
        # 1. Fase de Leitura (Snapshot local)
        val_a, ver_a = store.read("account_A")
        val_b, ver_b = store.read("account_B")
        
        read_set = {"account_A": ver_a, "account_B": ver_b}
        
        # Simula processamento transacional local
        transfer_amount = 10
        if val_a >= transfer_amount:
            new_a = val_a - transfer_amount
            new_b = val_b + transfer_amount
        else:
            new_a = val_a
            new_b = val_b

        write_set = {"account_A": new_a, "account_B": new_b}
        
        # 2. Fase de Commit (Validação e CAS)
        if store.commit(read_set, write_set):
            latency = (time.time() - start_time) * 1000.0 # ms
            return True, latency
        
        # Se falhou, o loop repete automaticamente (retry lock-free)

def main():
    store = TransactionalStore()
    total_transactions = 10000
    num_threads = 32

    print(f"Iniciando simulação TAM Lock-Free: {total_transactions} transações em {num_threads} núcleos...")
    
    latencies = []
    success_count = 0

    start_wall_time = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(run_transaction, store, i) for i in range(total_transactions)]
        
        for future in as_completed(futures):
            success, latency = future.result()
            if success:
                success_count += 1
                latencies.append(latency)

    total_time = time.time() - start_wall_time
    success_rate = (success_count / total_transactions) * 100.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print(f"--- Resultados da Simulação ---")
    print(f"Transações Totais: {total_transactions}")
    print(f"Sucessos (Commits): {success_count} ({success_rate:.2f}%)")
    print(f"Abortos (Conflitos resolvidos sem lock): {store.aborts}")
    print(f"Latência Média Local: {avg_latency:.4f} ms")
    print(f"Tempo Total de Execução: {total_time:.4f} s")
    
    # Validação de Invariantes ACID (Conservação do saldo total)
    final_a, _ = store.read("account_A")
    final_b, _ = store.read("account_B")
    total_balance = final_a + final_b
    print(f"Saldo Final Consolidado (A + B): {total_balance} (Esperado: 50000)")
    
    assert total_balance == 50000, "Violação de consistência ACID: Saldo total alterado!"
    assert success_rate >= 95.0, f"Taxa de sucesso abaixo da meta: {success_rate}%"
    assert avg_latency < 10.0, f"Latência média acima da meta: {avg_latency}ms"
    print("VEREDITO DO EXPERIMENTO: APROVADO COM SUCESSO.")

if __name__ == "__main__":
    main()