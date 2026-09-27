import threading
import time
from typing import Dict, List, Any, Optional

class TransactionAbortedException(Exception):
    pass

class Version:
    def __init__(self, value: Any, created_at: int):
        self.value = value
        self.created_at = created_at       # ID da transação que criou
        self.expired_at: Optional[int] = None # ID da transação que sobrescreveu

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
            # Encontra a versão visível para este tx_id (criada por tx <= tx_id e não expirada por tx <= tx_id)
            # Para simplificar e garantir snapshot isolation estrito:
            # Versão visível é aquela cujo created_at <= tx_id e (expired_at é None ou expired_at > tx_id)
            valid_version = None
            for v in versions:
                if v.created_at <= tx_id:
                    if v.expired_at is None or v.expired_at > tx_id:
                        valid_version = v
            
            return valid_version.value if valid_version else None

    def commit(self, tx_id: int, writes: dict) -> bool:
        with self._lock:
            # Validação de Conflito Write-Write:
            # Se alguma chave escrita por esta transação foi modificada (criada) por outra transação 
            # com ID > tx_id.start_ts (ou seja, cometida após o início desta transação), há conflito.
            for key in writes:
                versions = self._store.get(key, [])
                for v in versions:
                    # Se existe uma versão criada por uma transação posterior ao nosso início, conflito!
                    if v.created_at > tx_id:
                        self._abort_internal(tx_id)
                        raise TransactionAbortedException(f"Write-Write conflict em '{key}' para tx {tx_id}")

            # Se passou na validação, aplica as escritas
            for key, value in writes.items():
                if key not in self._store:
                    self._store[key] = []
                
                versions = self._store[key]
                # Expira a versão anterior ativa
                for v in versions:
                    if v.expired_at is None:
                        v.expired_at = tx_id

                # Adiciona a nova versão
                new_version = Version(value, created_at=tx_id)
                versions.append(new_version)

            self._active_transactions.remove(tx_id)
            return True

    def rollback(self, tx_id: int):
        with self._lock:
            if tx_id in self._active_transactions:
                self._active_transactions.remove(tx_id)

    def _abort_internal(self, tx_id: int):
        if tx_id in self._active_transactions:
            self._active_transactions.remove(tx_id)

class Transaction:
    def __init__(self, store: MVCCStore):
        self.store = store
        self.tx_id = store.begin_transaction()
        self.writes: Dict[str, Any] = {}
        self.status = "ACTIVE"

    def read(self, key: str) -> Any:
        if self.status != "ACTIVE":
            raise TransactionAbortedException("Transação não está ativa.")
        return self.store.read(self.tx_id, key, self.writes)

    def write(self, key: str, value: Any):
        if self.status != "ACTIVE":
            raise TransactionAbortedException("Transação não está ativa.")
        self.writes[key] = value

    def commit(self):
        if self.status != "ACTIVE":
            raise TransactionAbortedException("Transação não está ativa.")
        try:
            self.store.commit(self.tx_id, self.writes)
            self.status = "COMMITTED"
        except TransactionAbortedException:
            self.status = "ABORTED"
            raise

    def rollback(self):
        if self.status == "ACTIVE":
            self.store.rollback(self.tx_id)
            self.status = "ABORTED"

def test_snapshot_isolation_and_reads(store):
    print("Executando teste de leitura isolada...")
    tx1 = Transaction(store)
    tx1.write("saldo", 100)
    tx1.commit()

    # Tx2 inicia após o commit de tx1
    tx2 = Transaction(store)
    assert tx2.read("saldo") == 100

    # Tx3 modifica saldo para 200 mas ainda não comita
    tx3 = Transaction(store)
    tx3.write("saldo", 200)

    # Tx2 ainda deve enxergar 100 (Snapshot Isolation) e read-your-writes próprio
    assert tx2.read("saldo") == 100
    assert tx3.read("saldo") == 200

    tx3.commit()
    # Tx2 continua enxergando seu snapshot original (100)
    assert tx2.read("saldo") == 100
    tx2.commit()

    # Nova transação enxerga o valor atualizado (200)
    tx4 = Transaction(store)
    assert tx4.read("saldo") == 200
    tx4.commit()
    print("-> Teste de Snapshot Isolation passou com sucesso!")

def test_write_write_conflict_rollback(store):
    print("Executando teste de conflito de escrita-escrita e rollback automático...")
    tx_a = Transaction(store)
    tx_b = Transaction(store)

    # Ambas leem ou iniciam, TxA escreve e comita
    tx_a.write("contador", 15)
    tx_b.write("contador", 20)

    # TxA comita primeiro
    tx_a.commit()
    print("-> TxA comutou com sucesso.")

    # TxB tenta comitar, DEVE falhar por conflito de escrita-escrita
    try:
        tx_b.commit()
        raise AssertionError("Deveria ter lançado TransactionAbortedException!")
    except TransactionAbortedException as e:
        print(f"-> Sucesso: Conflito detectado corretamente -> {e}")
        tx_b.rollback()

def test_multithreaded_concurrency(store):
    print("Executando testes de concorrência com múltiplas threads...")
    
    def worker_writer(worker_id):
        try:
            tx = Transaction(store)
            val = tx.read("misto") or 0
            time.sleep(0.01)
            tx.write("misto", val + 1)
            tx.commit()
        except TransactionAbortedException:
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
    print(f"-> Valor final após concorrência de escritas: {final_val} (válido sob controle otimista)")
    tx_check.commit()

if __name__ == "__main__":
    store = MVCCStore()
    test_snapshot_isolation_and_reads(store)
    test_write_write_conflict_rollback(store)
    test_multithreaded_concurrency(store)
    print("Todos os testes de MVCC concluídos com sucesso.")