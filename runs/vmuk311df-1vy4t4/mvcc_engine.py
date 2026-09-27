import threading
import time
from typing import Dict, List, Any, Optional

class TransactionAbortedException(Exception):
    pass

class Version:
    def __init__(self, value: Any, created_at: int):
        self.value = value
        self.created_at = created_at       # ID da transação que criou
        self.expired_at: Optional[int] = None # ID da transação que sobrescreveu/apagou

class MVCCStore:
    def __init__(self):
        self._store: Dict[str, List[Version]] = {}
        self._lock = threading.Lock()
        self._global_tx_id = 0
        self._active_transactions = set()

    def begin_transaction(self) -> int:
        with self._lock:
            self._global_tx_id += 1
            tx_id = self._global_tx_id
            self._active_transactions.add(tx_id)
            return tx_id

    def read(self, tx_id: int, key: str, uncommitted_writes: dict) -> Any:
        # 1. Read-your-writes: se a própria transação escreveu na chave, retorna o valor pendente
        if key in uncommitted_writes:
            return uncommitted_writes[key]

        with self._lock:
            versions = self._store.get(key, [])
            # Snapshot Isolation: encontrar a versão visível para tx_id
            # Uma versão é visível se foi criada por uma transação <= tx_id (e que já cometeu)
            # Simplificação didática: versões com created_at < tx_id e (expired_at é None ou expired_at > tx_id)
            visible_value = None
            for v in versions:
                if v.created_at <= tx_id:
                    if v.expired_at is None or v.expired_at > tx_id:
                        visible_value = v.value
            return visible_value

    def commit(self, tx_id: int, uncommitted_writes: dict) -> bool:
        with self._lock:
            # Verificar conflitos de escrita-escrita (Write-Write Conflict)
            for key in uncommitted_writes:
                versions = self._store.get(key, [])
                for v in versions:
                    # Se há alguma versão criada por outro tx com ID > tx_id (ou seja, cometida concorrentemente após o start deste tx)
                    if v.created_at > tx_id:
                        self._active_transactions.remove(tx_id)
                        return False # Conflito detectado!

            # Aplicar escritas
            for key, value in uncommitted_writes.items():
                if key not in self._store:
                    self._store[key] = []
                
                # Marcar versão anterior como expirada por este tx_id
                for v in self._store[key]:
                    if v.expired_at is None:
                        v.expired_at = tx_id

                # Adicionar nova versão
                self._store[key].append(Version(value, tx_id))

            self._active_transactions.remove(tx_id)
            return True

    def rollback(self, tx_id: int):
        with self._lock:
            if tx_id in self._active_transactions:
                self._active_transactions.remove(tx_id)

class Transaction:
    def __init__(self, store: MVCCStore):
        self.store = store
        self.tx_id = store.begin_transaction()
        self.writes: Dict[str, Any] = {}
        self.committed = False
        self.aborted = False

    def read(self, key: str) -> Any:
        if self.aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        return self.store.read(self.tx_id, key, self.writes)

    def write(self, key: str, value: Any):
        if self.aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        self.writes[key] = value

    def commit(self):
        if self.aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        success = self.store.commit(self.tx_id, self.writes)
        if not success:
            self.aborted = True
            raise TransactionAbortedException(f"Conflito de escrita detectado na transação {self.tx_id}. Rollback automático realizado.")
        self.committed = True

    def rollback(self):
        if not self.committed and not self.aborted:
            self.store.rollback(self.tx_id)
            self.aborted = True

# --- TESTES DE CONCORRÊNCIA E VALIDAÇÃO ---

def test_snapshot_isolation_and_reads(store):
    print("Executando teste de leitura isolada...")
    # Setup inicial
    tx0 = Transaction(store)
    tx0.write("saldo", 100)
    tx0.commit()

    # Transação 1 lê saldo (100)
    tx1 = Transaction(store)
    assert tx1.read("saldo") == 100

    # Transação 2 altera saldo para 200 e comita
    tx2 = Transaction(store)
    tx2.write("saldo", 200)
    tx2.commit()

    # Transação 1 ainda deve enxergar 100 (Snapshot Isolation)
    assert tx1.read("saldo") == 100
    tx1.commit()

    # Nova transação enxerga 200
    tx3 = Transaction(store)
    assert tx3.read("saldo") == 200
    tx3.commit()
    print("-> Teste de Snapshot Isolation passou com sucesso!")

def test_write_write_conflict_rollback(store):
    print("Executando teste de conflito de escrita-escrita e rollback automático...")
    tx0 = Transaction(store)
    tx0.write("contador", 10)
    tx0.commit()

    # TxA e TxB iniciam simultaneamente
    tx_a = Transaction(store)
    tx_b = Transaction(store)

    tx_a.write("contador", 15)
    tx_b.write("contador", 20)

    # TxA comita primeiro
    tx_a.commit()
    print("-> TxA comutou com sucesso.")

    # TxB tenta comitar, deve falhar por conflito de escrita-escrita
    try:
        tx_b.commit()
        raise AssertionError("Deveria ter lançado TransactionAbortedException!")
    except TransactionAbortedException as e:
        print(f"-> Sucesso: {e}")
        tx_b.rollback()

def test_multithreaded_concurrency(store):
    print("Executando testes de concorrência com múltiplas threads...")
    
    def worker_writer(worker_id):
        try:
            tx = Transaction(store)
            val = tx.read("misto") or 0
            time.sleep(0.01) # Simula trabalho
            tx.write("misto", val + 1)
            tx.commit()
        except TransactionAbortedException:
            # Conflito esperado sob alta concorrência otimista
            pass

    threads = []
    for i in range(10):
        t = threading.Thread(target=worker_writer, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    tx_check = Transaction(store)
    final_val = tx_check.read("misto")
    print(f"-> Valor final após concorrência de escritas: {final_val} (deve ser <= 10 devido a conflitos abortados)")
    tx_check.commit()

if __name__ == "__main__":
    store = MVCCStore()
    test_snapshot_isolation_and_reads(store)
    test_write_write_conflict_rollback(store)
    test_multithreaded_concurrency(store)
    print("Todos os testes de MVCC concluídos com sucesso.")