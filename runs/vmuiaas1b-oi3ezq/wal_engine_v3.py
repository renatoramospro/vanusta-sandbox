import os
import threading
import zlib

class WriteAheadLogV3:
    def __init__(self, log_file="wal_v3.log"):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.lsn_counter = 0
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        open(self.log_file, "w").close()

    def append(self, tx_id, key, value):
        """Escreve no WAL com LSN, dados e um checksum CRC32 para integridade contra truncamentos."""
        with self.lock:
            self.lsn_counter += 1
            current_lsn = self.lsn_counter
            # Payload bruto a ser checado
            payload = f"{current_lsn},{tx_id},{key},{value}"
            # Calcula o checksum CRC32 do payload
            checksum = zlib.crc32(payload.encode('utf-8')) & 0xffffffff
            log_entry = f"{payload},{checksum}\n"
            
            with open(self.log_file, "a") as f:
                f.write(log_entry)
                f.flush()
                os.fsync(f.fileno())

    def recover(self):
        """
        Lê o WAL aplicando REDO com validação estrita de LSN monotônico 
        e verificação de integridade via Checksum (CRC32).
        """
        store = {}
        if not os.path.exists(self.log_file):
            return store

        last_lsn = -1
        with open(self.log_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = line.split(",")
                    # Formato esperado: LSN, TX_ID, KEY, VALUE, CHECKSUM (5 campos)
                    if len(parts) != 5:
                        # Linha truncada ou com número incorreto de campos
                        break 
                    
                    lsn_str, tx_id, key, value, checksum_str = parts
                    lsn = int(lsn_str)
                    file_checksum = int(checksum_str)
                    
                    # Validação de monotonicidade do LSN
                    if lsn <= last_lsn:
                        break # Ordem violada, para a recuperação
                    
                    # Validação de integridade via CRC32 do payload original
                    payload = f"{lsn_str},{tx_id},{key},{value}"
                    calculated_checksum = zlib.crc32(payload.encode('utf-8')) & 0xffffffff
                    
                    if calculated_checksum != file_checksum:
                        # Checksum inválido indica corrupção de dados na linha
                        break
                    
                    last_lsn = lsn
                    store[key] = value
                    
                except (ValueError, UnicodeDecodeError):
                    # Erro de parsing ou conversão numérica encerra o REDO com segurança
                    break
                    
        return store

class DatabaseWithWAL:
    def __init__(self, log_file="wal_v3.log"):
        self.wal = WriteAheadLogV3(log_file)
        self.store = {}
        self.store_lock = threading.Lock()

    def put(self, tx_id, key, value):
        self.wal.append(tx_id, key, value)
        with self.store_lock:
            self.store[key] = value

    def simulate_crash_and_recover(self):
        with self.store_lock:
            self.store.clear()
        self.store = self.wal.recover()

if __name__ == "__main__":
    db = DatabaseWithWAL()
    total_threads = 10
    items_per_thread = 100
    total_transactions = total_threads * items_per_thread

    def worker(t_id):
        for i in range(items_per_thread):
            tx_id = f"tx_{t_id}_{i}"
            key = f"key_{t_id}_{i}"
            val = f"val_{i}"
            db.put(tx_id, key, val)

    print("Iniciando transações concorrentes com LSN e Checksum...")
    threads = []
    for t_id in range(total_threads):
        th = threading.Thread(target=worker, args=(t_id,))
        threads.append(th)
        th.start()

    for th in threads:
        th.join()

    print(f"Total de {total_transactions} transações concorrentes executadas.")
    
    # CENÁRIO ADVERSARIAL: Simula corrupção de log com linha truncada/adulterada
    print("Injetando linha corrompida (checksum inválido) no final do arquivo de log...")
    with open(db.wal.log_file, "a") as f:
        # Linha com 5 campos, mas checksum totalmente incorreto e dados falsos
        f.write("99999,tx_corrupted,key_fake,val_fa,12345678\n")

    count_before = len(db.store)

    print("[Simulação] Encerramento abrupto (Crash) disparado! Memória limpa.")
    db.simulate_crash_and_recover()

    with db.store_lock:
        count_after = len(db.store)

    print(f"Itens na memória antes do crash: {count_before}")
    print(f"Itens na memória após recuperação com validação de checksum: {count_after}")

    # Validações estritas
    assert count_before == total_transactions, "Erro: Estado inconsistente antes do crash!"
    assert count_after == total_transactions, f"Erro: A recuperação falhou ao aceitar o log corrompido! Esperado {total_transactions}, obtido {count_after}."
    
    # Amostragem de integridade lógica
    assert db.store.get("key_5_50") == "val_50", "Erro de integridade nos dados recuperados!"

    print("SUCESSO: Recuperação robusta validada com LSN, Checksum e rejeição de dados corrompidos!")