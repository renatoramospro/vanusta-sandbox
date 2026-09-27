import threading
import time
from typing import Dict, List, Any, Optional, Set

class TransactionAbortedException(Exception):
    pass

class Version:
    def __init__(self, value: Any, created_at: int):
        self.value = value
        self.created_at = created_at       # Timestamp da transação que criou esta versão
        self.expired_at: Optional[int] = None # Timestamp da transação que expirou/sobrescreveu esta versão

class MVCCStore:
    def __init__(self):
        self._store: Dict[str, List[Version]] = {}
        # Histórico de commits: lista de tuplas (commit_ts, write_set)
        self._committed_transactions: List[tuple] = []
        self._lock = threading.Lock()
        self._global_ts = 0

    def get_timestamp(self) -> int:
        with self._lock:
            self._global_ts += 1
            return self._global_ts

    def read(self, tx_id: int, key: str, uncommitted_writes: dict) -> Any:
        # Read-your-writes: se a própria transação escreveu na chave, retorna o valor pendente
        if key in uncommitted_writes:
            return uncommitted_writes[key]

        with self._lock:
            versions = self._store.get(key, [])
            # Snapshot Isolation: visível se foi criada por uma transação com commit_ts <= tx_id (start_ts)
            # ou criada pela própria transação, e não expirada antes de tx_id.
            visible_value = None
            for v in versions:
                if v.created_at <= tx_id:
                    if v.expired_at is None or v.expired_at > tx_id:
                        visible_value = v.value
            return visible_value

    def commit(self, tx_id: int, write_set: Set[str]) -> None:
        with self._lock:
            # Validação Optimistic Concurrency Control (OCC) para Conflitos Write-Write:
            # Verifica se alguma transação comitou alterações em QUALQUER chave do nosso write_set
            # APÓS o start_ts desta transação (tx_id).
            for commit_ts, committed_keys in self._committed_transactions:
                if commit_ts > tx_id:
                    # Há sobreposição de chaves escritas?
                    if not write_set.isdisjoint(committed_keys):
                        raise TransactionAbortedException(
                            f"Conflito Write-Write detectado: Tx {tx_id} tentou escrever em chaves já comitadas após seu início."
                        )

            # Se não há conflito, efetiva as escritas
            current_time = self.get_timestamp()
            for key, value in write_set.items() if hasattr(write_set, 'items') else []:
                pass # Tratado no objeto Transaction

            # Registra o commit globalmente
            self._committed_transactions.append((current_time, set(write_set)))

    def apply_writes(self, tx_id: int, writes: dict):
        with self._lock:
            for key, value in writes.items():
                if key not in self._store:
                    self._store[key] = []
                
                versions = self._store[key]
                # Expira a versão ativa anterior
                for v in versions:
                    if v.expired_at is None:
                        v.expired_at = tx_id

                # Adiciona a nova versão criada por esta transação
                new_version = Version(value, created_at=tx_id)
                versions.append(new_version)

class Transaction:
    def __init__(self, store: MVCCStore):
        self.store = store
        self.start_ts = store.get_timestamp()
        self._writes: Dict[str, Any] = {}
        self._aborted = False

    def read(self, key: str) -> Any:
        if self._aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        return self.store.read(self.start_ts, key, self._writes)

    def write(self, key: str, value: Any):
        if self._aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        self._writes[key] = value

    def commit(self):
        if self._aborted:
            raise TransactionAbortedException("Transação já foi abortada.")
        try:
            # Valida e comita no store
            self.store.commit(self.start_ts, set(self._writes.keys()))
            if self._writes:
                self.store.apply_writes(self.start_ts, self._writes)
        except TransactionAbortedException:
            self._aborted = True
            self.rollback()
            raise

    def rollback(self):
        self._aborted = True
        self._writes.clear()

def test_snapshot_isolation_and_reads(store):
    print("Executando teste de leitura isolada...")
    tx1 = Transaction(store)
    tx1.write("saldo", 100)
    tx1.commit()

    # Tx2 inicia antes da alteração de Tx3
    tx2 = Transaction(store)
    
    tx3 = Transaction(store)
    tx3.write("saldo", 250)
    tx3.commit()

    # Tx2 deve ver o snapshot antigo (100), garantindo Snapshot Isolation
    val_tx2 = tx2.read("saldo")
    assert val_tx2 == 100, f"Esperado 100, obtido {val_tx2}"
    tx2.commit()

    # Nova transação deve ver o valor atualizado (250)
    tx4 = Transaction(store)
    assert tx4.read("saldo") == 250
    tx4.commit()
    print("-> Teste de Snapshot Isolation passou com sucesso!")

def test_write_write_conflict_rollback(store):
    print("Executando teste de conflito de escrita-escrita e rollback automático...")
    tx_a = Transaction(store)
    tx_b = Transaction(store)

    tx_a.write("contador", 15)
    tx_b.write("contador", 20)

    # TxA comuta com sucesso
    tx_a.commit()
    print("-> TxA comutou com sucesso.")

    # TxB tenta comitar, DEVE falhar por conflito de escrita-escrita
    try:
        tx_b.commit()
        raise AssertionError("Deveria ter lançado TransactionAbortedException!")
    except TransactionAbortedException as e:
        print(f"-> Sucesso: Conflito detectado corretamente -> {e}")
        # Rollback automático já é chamado no except/commit da transaction
        assert tx_b._aborted is True

def test_multithreaded_concurrency(store):
    print("Executando testes de concorrência com múltiplas threads...")
    
    def worker_writer(worker_id):
        try:
            tx = Transaction(store)
            val = tx.read("misto") or 0
            time.sleep(0.001)
            tx.write("misto", val + 1)
            tx.commit()
        except TransactionAbortedException:
            pass # Conflitos OCC em alta concorrência são esperados e tratados via retry/abort

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