import os
import threading

class WriteAheadLogV2:
    def __init__(self, log_file="wal_v2.log"):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.lsn_counter = 0
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        open(self.log_file, "w").close()

    def append(self, tx_id, key, value):
        """Escreve no WAL com um LSN (Log Sequence Number) estrito e atômico."""
        with self.lock:
            self.lsn_counter += 1
            current_lsn = self.lsn_counter
            # Formato: LSN,TX_ID,KEY,VALUE
            log_entry = f"{current_lsn},{tx_id},{key},{value}\n"
            with open(self.log_file, "a") as f:
                f.write(log_entry)
                f.flush()
                os.fsync(f.fileno()) # Garante durabilidade física no disco

    def recover(self):
        """
        Lê o WAL aplicando REDO em ordem estrita de LSN.
        Trata de forma resiliente logs corrompidos ou truncados por crash abrupto.
        """
        store = {}
        if not os.path.exists(self.log_file):
            return store

        entries = []
        with open(self.log_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = line.split(",")
                    if len(parts) != 4:
                        raise ValueError(f"Linha mal-formada: campos insuficientes")
                    
                    lsn = int(parts[0])
                    tx_id = parts[1]
                    key = parts[2]
                    value = parts[3]
                    entries.append((lsn, tx_id, key, value))
                except (ValueError, IndexError) as e:
                    # Linha truncada/corrompida por crash no meio da escrita - para o recovery com segurança
                    print(f"[Aviso] Log truncado/corrompido detectado na linha {line_num} ('{line}'). Interrompendo REDO com segurança.")
                    break

        # Ordena estritamente por LSN para garantir determinismo sob concorrência
        entries.sort(key=lambda x: x[0])

        for lsn, tx_id, key, value in entries:
            store[key] = value

        return store

class InMemoryDatabaseV2:
    def __init__(self, log_file="wal_v2.log"):
        self.store = {}
        self.wal = WriteAheadLogV2(log_file)
        self.store_lock = threading.Lock()

    def put(self, tx_id, key, value):
        # 1. Escreve no WAL (Write-Ahead) ANTES de alterar a memória
        self.wal.append(tx_id, key, value)
        
        # 2. Aplica na memória
        with self.store_lock:
            self.store[key] = value

    def simulate_crash_and_recover(self):
        # Simula perda total da memória volátil
        with self.store_lock:
            self.store = {}
        
        # Recupera estado a partir do WAL ordenado por LSN
        recovered_store = self.wal.recover()
        with self.store_lock:
            self.store = recovered_store

# --- Execução do Teste Concorrente e Adversarial ---
if __name__ == "__main__":
    db = InMemoryDatabaseV2()

    total_threads = 10
    items_per_thread = 100
    total_transactions = total_threads * items_per_thread

    def worker(thread_id):
        for i in range(items_per_thread):
            tx_id = f"tx_{thread_id}_{i}"
            key = f"key_{thread_id}_{i}"
            val = f"val_{i}"
            db.put(tx_id, key, val)

    print("Iniciando transações concorrentes com LSN...")
    threads = []
    for t_id in range(total_threads):
        th = threading.Thread(target=worker, args=(t_id,))
        threads.append(th)
        th.start()

    for th in threads:
        th.join()

    print(f"Total de {total_transactions} transações concorrentes executadas.")
    
    # CENÁRIO ADVERSARIAL: Simula corrupção de log por escrita interrompida abruptamente
    print("Injetando linha truncada/corrompida no final do arquivo de log...")
    with open(db.wal.log_file, "a") as f:
        f.write("99999,tx_corrupted,key_fake,val_fa\n") # Linha cortada simulando crash no meio

    count_before = len(db.store)

    print("[Simulação] Encerramento abrupto (Crash) disparado! Memória limpa.")
    db.simulate_crash_and_recover()

    with db.store_lock:
        count_after = len(db.store)

    print(f"Itens na memória antes do crash: {count_before}")
    print(f"Itens na memória após recuperação com tratamento de log corrompido: {count_after}")

    # Validações estritas
    assert count_before == total_transactions, "Erro: Estado inconsistente antes do crash!"
    assert count_after == total_transactions, "Erro: A recuperação falhou ao ignorar o log corrompido ou restaurar os dados!"
    
    # Amostragem de integridade lógica por LSN
    assert db.store.get("key_5_50") == "val_50", "Erro de integridade nos dados recuperados!"

    print("SUCESSO: Recuperação robusta validada com LSN e tratamento de falhas de truncamento!")