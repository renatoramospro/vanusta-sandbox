import threading
import time
from typing import Dict, Set, List, Optional

class DeadlockException(Exception):
    """Exceção lançada quando um deadlock é detectado e a transação é abortada."""
    pass

class UnauthorizedTransactionException(Exception):
    """Exceção lançada quando há tentativa de spoofing ou acesso não autorizado."""
    pass

class ResourceGraphManager:
    """
    Gerenciador de Recursos com motor de detecção de deadlocks baseado em Wait-For Graph (WFG)
    e endurecimento de segurança (autenticação de transações, limpeza atômica e DFS iterativa).
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.holder: Dict[str, str] = {}           # recurso -> transação dona
        self.waiter: Dict[str, str] = {}           # transação -> recurso que ela está esperando
        self.tx_owners: Dict[str, str] = {}        # transação -> token de autenticação do dono
        self.aborted_transactions: Set[str] = set()

    def _register_tx_if_needed(self, tx: str, auth_token: str):
        if tx not in self.tx_owners:
            self.tx_owners[tx] = auth_token
        elif self.tx_owners[tx] != auth_token:
            raise UnauthorizedTransactionException(
                f"Acesso negado: Transação '{tx}' pertence a outro contexto de segurança."
            )

    def _has_cycle_iterative(self, start_tx: str) -> Optional[List[str]]:
        """
        Detecta ciclos no WFG usando busca em profundidade iterativa com pilha explícita.
        Evita RecursionError em grafos profundos.
        """
        visited = set()
        stack = [(start_tx, [start_tx])]

        while stack:
            current, path = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            # Descobre quais recursos a transação 'current' está esperando
            waiting_resource = self.waiter.get(current)
            if not waiting_resource:
                continue
            
            # Descobre quem detém esse recurso
            holder_tx = self.holder.get(waiting_resource)
            if holder_tx:
                if holder_tx == start_tx:
                    return path + [holder_tx]
                if holder_tx not in visited:
                    stack.append((holder_tx, path + [holder_tx]))
        return None

    def request_resource(self, tx: str, resource: str, auth_token: str) -> bool:
        with self.lock:
            self._register_tx_if_needed(tx, auth_token)

            # Se o recurso está livre, aloca imediatamente
            if resource not in self.holder:
                self.holder[resource] = tx
                # Se estava esperando algo antes e conseguiu, remove da espera
                if self.waiter.get(tx) == resource:
                    del self.waiter[tx]
                return True

            owner = self.holder[resource]
            if owner == tx:
                return True  # Já possui o recurso

            # Registra espera
            self.waiter[tx] = resource

            # Verifica ciclo no WFG usando DFS iterativa
            cycle = self._has_cycle_iterative(tx)
            if cycle:
                cycle_str = " -> ".join(cycle)
                # Aborto e limpeza atômica da transação causadora
                self._abort_transaction(tx)
                raise DeadlockException(f"Deadlock detectado no ciclo [{cycle_str}]. Transação {tx} abortada.")

            return False

    def release_resources(self, tx: str, auth_token: str):
        with self.lock:
            if tx in self.tx_owners and self.tx_owners[tx] != auth_token:
                raise UnauthorizedTransactionException(f"Tentativa de liberação não autorizada para '{tx}'.")

            # Libera todos os recursos detidos pela transação
            resources_to_free = [res for res, owner in self.holder.items() if owner == tx]
            for res in resources_to_free:
                del self.holder[res]
            
            if tx in self.waiter:
                del self.waiter[tx]
            if tx in self.tx_owners:
                del self.tx_owners[tx]

    def _abort_transaction(self, tx: str):
        """Remove ativamente todos os rastros da transação abortada para evitar estado fantasma."""
        self.aborted_transactions.add(tx)
        # Libera recursos detidos
        resources_to_free = [res for res, owner in self.holder.items() if owner == tx]
        for res in resources_to_free:
            del self.holder[res]
        # Remove arestas de espera
        if tx in self.waiter:
            del self.waiter[tx]
        if tx in self.tx_owners:
            del self.tx_owners[tx]

def test_security_and_spoofing():
    manager = ResourceGraphManager()
    manager.request_resource("T1", "R1", "token-A")
    
    # Tentativa de spoofing: outra entidade tentando acessar T1 com token incorreto
    try:
        manager.request_resource("T1", "R2", "token-B")
        assert False, "Deveria ter bloqueado acesso não autorizado"
    except UnauthorizedTransactionException:
        print("Teste de segurança (prevenção de spoofing) passou com sucesso.")

def test_deadlock_detection_iterative_and_atomic_cleanup():
    manager = ResourceGraphManager()
    assert manager.request_resource("T1", "R1", "token-1") == True
    assert manager.request_resource("T2", "R2", "token-2") == True
    assert manager.request_resource("T1", "R2", "token-1") == False

    try:
        manager.request_resource("T2", "R1", "token-2")
        assert False, "Deveria disparar deadlock"
    except DeadlockException as e:
        print(f"Deadlock capturado com sucesso (DFS iterativa): {e}")

    # Verifica limpeza atômica: T2 deve ter sido purgada completamente do holder e waiter
    assert "T2" not in manager.holder.values()
    assert "T2" not in manager.waiter
    print("Teste de limpeza atômica de estado concluído com sucesso.")

def test_concurrent_threads():
    manager = ResourceGraphManager()
    errors = []

    def worker(tx_id, r1, r2, token):
        try:
            manager.request_resource(tx_id, r1, token)
            time.sleep(0.005)
            manager.request_resource(tx_id, r2, token)
        except DeadlockException:
            pass
        except Exception as ex:
            errors.append(ex)

    t1 = threading.Thread(target=worker, args=("T1", "R1", "R2", "token-1"))
    t2 = threading.Thread(target=worker, args=("T2", "R2", "R1", "token-2"))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(errors) == 0, fErros inesperados em concorrência: {errors}"
    print("Teste com múltiplas threads concorrentes executado com sucesso.")

if __name__ == "__main__":
    print("Iniciando testes rigorosos de segurança, robustez e concorrência...")
    test_security_and_spoofing()
    test_deadlock_detection_iterative_and_atomic_cleanup()
    test_concurrent_threads()
    print("Todos os testes de segurança e concorrência passaram com sucesso absoluto!")