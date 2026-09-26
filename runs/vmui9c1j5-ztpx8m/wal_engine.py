import os
import threading
import time

class WriteAheadLog:
    def __init__(self, log_file="wal.log"):
        self.log_file = log_file
        self.lock = threading.Lock()
        # Inicializa o arquivo de log se não existir
        if not os.path.exists(self.log_file):
            open(self.log_file, "w").close()

    def append(self, tx_id, key, value):
        """Escreve a transação no log ANTES de aplicar na memória (Write-Ahead)."""
        with self.lock:
            with open(self.log_file, "a") as f:
                f.write(f"{tx_id},{key},{value}\n")
                f.flush()
                os.fsync(f.fileno())  # Garante durabilidade física no disco

    def recover(self):
        """Lê o log e reconstrói o estado consistente (REDO)."""
        state = {}
        if not os.path.exists(self.log_file):
            return state
        
        with open(self.log_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) == 3:
                    tx_id, key, value = parts
                    # Redo: aplica a última alteração válida encontrada no log
                    state[key] = value
        return state

class InMemoryDatabaseWithWAL:
    def __init__(self, log_file="wal.log"):
        self.wal = WriteAheadLog(log_file)
        self.store = {}
        self.store_lock = threading.Lock()

    def set(self, tx_id, key, value):
        # 1. WAL: Grava no log primeiro
        self.wal.append(tx_id, key, value)
        
        # 2. Aplica na memória
        with self.store_lock:
            self.store[key] = value

    def crash_and_recover(self):
        """Simula um encerramento abrupto destruindo a memória e recuperando via WAL."""
        print("[Simulação] Encerramento abrupto (Crash) disparado! Memória limpa.")
        with self.store_lock:
            self.store = {}
        
        # Recuperação
        recovered_state = self.wal.recover()
        with self.store_lock:
            self.store = recovered_state
        print(f"[Recuperação] Estado recuperado com sucesso a partir do WAL.")

def worker(db, start_id, count):
    """Executa transações concorrentes."""
    for i in range(count):
        tx_id = f"tx_{start_id}_{i}"
        key = f"key_{start_id}_{i}"
        value = f"val_{i}"
        db.set(tx_id, key, value)

if __name__ == "__main__":
    log_path = "test_wal.log"
    # Limpa log anterior se houver
    if os.path.exists(log_path):
        os.remove(log_path)

    db = InMemoryDatabaseWithWAL(log_file=log_path)

    print("Iniciando transações concorrentes (Simulando carga)...")
    threads = []
    num_threads = 10
    items_per_thread = 100  # Total de 1000 transações concorrentes

    for t in range(num_threads):
        th = threading.Thread(target=worker, args=(db, t, items_per_thread))
        threads.append(th)
        th.start()

    for th in threads:
        th.join()

    total_transactions_executed = num_threads * items_per_thread
    print(f"Total de {total_transactions_executed} transações executadas e gravadas no WAL.")
    
    # Valida estado antes do crash
    with db.store_lock:
        count_before = len(db.store)

    # Simula crash abrupto e recuperação
    db.crash_and_recover()

    # Validação pós-recuperação
    with db.store_lock:
        count_after = len(db.store)

    print(f"Itens na memória antes do crash: {count_before}")
    print(f"Itens na memória após recuperação: {count_after}")

    # Validação rigorosa do critério de sucesso
    assert count_before == total_transactions_executed, "Erro: Estado inconsistente antes do crash!"
    assert count_after == total_transactions_executed, "Erro: Falha na recuperação de 100% dos dados pelo WAL!"
    
    # Amostragem de integridade
    sample_key = "key_0_50"
    assert db.store.get(sample_key) == "val_50", f"Erro de integridade para a chave {sample_key}!"
    
    print("SUCESSO: 100% do estado consistente recuperado a partir do WAL após falha simulada!")

    # Limpeza final do arquivo de teste
    if os.path.exists(log_path):
        os.remove(log_path)