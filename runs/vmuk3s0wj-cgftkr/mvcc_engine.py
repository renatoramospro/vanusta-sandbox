import threading
import time
from typing import Dict, List, Any, Optional, Set

class TransactionAbortedException(Exception):
    pass

class Version:
    def __init__(self, value: Any, created_at: int):
        self.value = value
        self.created_at = created_at       # ID / timestamp da transação que criou
        self.expired_at: Optional[int] = None # ID da transação que sobrescreveu

class MVCCStore:
    def __init__(self):
        self._store: Dict[str, List[Version]] = {}
        # Mapeia tx_id para o conjunto de chaves que ela modificou (para validação de conflito)
        self._committed_writes: Dict[int, Set[str]] = {}
        self._lock = threading.Lock()
        self._global_tx_id = 0

    def begin_transaction(self) -> int:
        with self._lock:
            self._global_tx_id += 1
            return self._global_tx_id

    def read(self, tx_id: int, key: str, uncommitted_writes: dict) -> Any:
        # Read-your-writes: se a própria transação escreveu na chave, retorna o valor pendente
        if key in uncommitted_writes:
            return uncommitted_writes[key]

        with self._lock:
            versions = self._store.get(key, [])
            # Encontra a versão visível para a transação com start_ts = tx_id
            # Uma versão é visível se foi criada por uma transação que já havia terminado antes de tx_id iniciar (created_at < tx_id)
            # E não foi expirada por uma transação com commit anterior, ou a versão atual.
            visible_value = None
            for v in versions:
                if v.created_at <= tx_id:
                    if v.expired_at is None or v.expired_at > tx_id:
                        visible_value = v.value
            return visible_value

    def commit(self, tx_id: int, uncommitted_writes: dict) -> None:
        with self._lock:
            # Validação de Conflito de Escrita-Escrita (Write-Write Conflict)
            # Verifica se alguma transação concorrente comitou alterações nas mesmas chaves
            for key in uncommitted_writes.keys():
                versions = self._store.get(key, [])
                for v in versions:
                    # Se existe uma versão criada por uma transação que rodou depois do nosso start_ts (created_at > tx_id)
                    # e essa transação já comitou (está em _committed_writes), há conflito!
                    if v.created_at > tx_id and v.created_at in self._committed_writes:
                        raise TransactionAbortedException(
                            f"Conflito de escrita-escrita detectado na chave '{key}' entre Tx {tx_id} e Tx {v.created_at}"
                        )

            # Se passou na validação, aplica as escritas
            self._committed_writes[tx_id] = set(uncommitted_writes.keys())
            for key, val in uncommitted_writes.items():
                if key not in self._store:
                    self._store[key] = []
                
                # Expira versões ativas anteriores
                for v in self._store[key]:
                    if v.expired_at is None:
                        v.expired_at = tx_id

                # Insere a nova versão
                new_version = Version(val, created_at=tx_id)
                self._store[key].append(new_version)

    def rollback(self, tx_id: int) -> None:
        # Em MVCC otimista, o rollback de transações abortadas simplesmente limpa o estado local
        pass

class Transaction:
    def __init__(self, store: MVCCStore):
        self.store = store
        self.tx_id = store.begin_transaction()
        self.uncommitted_writes: Dict[str, Any] = {}
        self.aborted = False

    def read(self, key: str) -> Any:
        if self.aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        return self.store.read(self.tx_id, key, self.uncommitted_writes)

    def write(self, key: str, value: Any) -> None:
        if self.aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        self.uncommitted_writes[key] = value

    def commit(self) -> None:
        if self.aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        try:
            self.store.commit(self.tx_id, self.uncommitted_writes)
        except TransactionAbortedException as e:
            self.aborted = True
            self.store.rollback(self.tx_id)
            raise e

    def rollback(self) -> None:
        self.aborted = True
        self.store.rollback(self.tx_id)

def test_snapshot_isolation_and_reads(store):
    print("Executando teste de leitura isolada...")
    tx1 = Transaction(store)
    tx1.write("saldo", 100)
    tx1.commit()

    # Tx2 inicia após Tx1 comitar
    tx2 = Transaction(store)
    assert tx2.read("saldo") == 100

    # Tx3 inicia em paralelo e escreve 200
    tx3 = Transaction(store)
    tx3.write("saldo", 200)
    tx3.commit()

    # Tx2 deve continuar vendo 100 (Snapshot Isolation)
    assert tx2.read("saldo") == 100, f"Esperado 100, obtido {tx2.read('saldo')}"
    tx2.commit()
    print("-> Teste de Snapshot Isolation passou com sucesso!")

def test_write_write_conflict_rollback(store):
    print("Executando teste de conflito de escrita-escrita e rollback automático...")
    tx_base = Transaction(store)
    tx_base.write("contador", 10)
    tx_base.commit()

    # TxA e TxB iniciam no mesmo instante (mesmo start_ts aparente)
    tx_a = Transaction(store)
    tx_b = Transaction(store)

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
            time.sleep(0.005)
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