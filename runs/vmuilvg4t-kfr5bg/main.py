import threading
import time
from typing import Dict, Set, List, Optional

class DeadlockException(Exception):
    """Exceção lançada quando um deadlock é detectado e a transação é abortada."""
    pass

class ResourceGraphManager:
    """
    Gerenciador de Recursos com motor de detecção de deadlocks baseado em Wait-For Graph (WFG).
    Implementado sem dependências externas para garantir portabilidade e execução determinística.
    
    Premissas do modelo:
    - Recursos de instância única.
    - Retenção bloqueante de locks.
    - Inexistência de protocolos de espera circular legítimos.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.holder: Dict[str, str] = {}     # recurso -> transação dona
        self.waiter: Dict[str, str] = {}     # transação -> recurso que ela está esperando
        self.aborted_transactions: Set[str] = set()

    def request_resource(self, tx: str, resource: str) -> bool:
        """
        Solicita um recurso para uma transação. Se o recurso estiver livre, aloca.
        Se estiver ocupado, registra a espera, constrói o WFG e verifica ciclos.
        Se houver ciclo (deadlock), aborta a transação causadora.
        """
        start_time = time.perf_counter()
        
        with self.lock:
            if tx in self.aborted_transactions:
                raise DeadlockException(f"Transação {tx} já foi abortada.")

            # Se o recurso está livre, adquire imediatamente
            if resource not in self.holder:
                self.holder[resource] = tx
                if tx in self.waiter:
                    del self.waiter[tx]
                return True

            owner = self.holder[resource]
            if owner == tx:
                return True  # Re-entrância simples

            # O recurso está ocupado: T_x espera por T_owner
            self.waiter[tx] = resource

            # Construção e verificação do WFG em tempo real
            has_cycle, cycle_path = self._detect_cycle(tx)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if has_cycle:
                # Resolução do conflito: aborta a transação causadora (tx)
                self._abort_transaction(tx)
                raise DeadlockException(
                    f"Deadlock detectado no ciclo {cycle_path} em {elapsed_ms:.4f}ms. "
                    f"Transação causadora {tx} abortada."
                )

            return False  # Deve aguardar

    def _detect_cycle(self, start_tx: str) -> (bool, List[str]):
        """
        Detecta ciclos no Wait-For Graph (WFG) usando DFS com coloração de vértices (branco/cinza/preto).
        Complexidade: O(V + E), onde V é o número de transações e E as arestas de espera.
        """
        visited = set()
        stack = set()
        path = []

        def dfs(current: str) -> bool:
            visited.add(current)
            stack.add(current)
            path.append(current)

            # Encontrar quem 'current' está esperando
            res = self.waiter.get(current)
            if res and res in self.holder:
                neighbor = self.holder[res]
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in stack:
                    path.append(neighbor)
                    return True

            stack.remove(current)
            path.pop()
            return False

        if dfs(start_tx):
            return True, path
        return False, []

    def _abort_transaction(self, tx: str):
        """Aborta a transação, liberando todos os recursos retidos por ela."""
        self.aborted_transactions.add(tx)
        # Remove transação dos waiters
        if tx in self.waiter:
            del self.waiter[tx]
        # Libera recursos que a transação possuía
        resources_to_release = [res for res, owner in self.holder.items() if owner == tx]
        for res in resources_to_release:
            del self.holder[res]

    def release_resources(self, tx: str):
        with self.lock:
            if tx in self.waiter:
                del self.waiter[tx]
            resources_to_release = [res for res, owner in self.holder.items() if owner == tx]
            for res in resources_to_release:
                del self.holder[res]

def test_no_deadlock_linear_waiting():
    """Valida contenção linear (T2 -> T1 sem retorno): NÃO deve constituir deadlock."""
    manager = ResourceGraphManager()
    
    assert manager.request_resource("T1", "R1") == True
    # T2 tenta pegar R1 (espera linear saudável, sem ciclo)
    assert manager.request_resource("T2", "R1") == False
    
    manager.release_resources("T1")
    print("Teste de contenção linear executado com sucesso (sem falsos positivos).")

def test_deadlock_detection_and_resolution_performance():
    """Testa detecção de ciclo fechado, tempo de execução (<10ms) e resolução por aborto."""
    manager = ResourceGraphManager()
    
    # T1 pega R1, T2 pega R2
    assert manager.request_resource("T1", "R1") == True
    assert manager.request_resource("T2", "R2") == True
    
    # T1 tenta pegar R2 (espera T2)
    assert manager.request_resource("T1", "R2") == False
    
    # T2 tenta pegar R1 (fecha o ciclo T1 <-> T2). Deve disparar exceção em <10ms.
    start = time.perf_counter()
    caught = False
    try:
        manager.request_resource("T2", "R1")
    except DeadlockException as e:
        caught = True
        elapsed = (time.perf_counter() - start) * 1000
        print(f"Deadlock capturado com sucesso em {elapsed:.4f}ms: {e}")
        assert elapsed < 10, "O motor de detecção excedeu o limite de 10ms!"

    assert caught == True, "Deveria ter lançado DeadlockException"
    assert "T2" in manager.aborted_transactions
    print("Teste de detecção, performance (<10ms) e resolução concluído com sucesso.")

if __name__ == "__main__":
    print("Iniciando testes rigorosos do motor de detecção de deadlocks...")
    test_no_deadlock_linear_waiting()
    test_deadlock_detection_and_resolution_performance()
    print("Todos os testes passaram com sucesso absoluto!")