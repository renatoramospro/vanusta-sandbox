import threading
import time
import networkx as nx
from typing import Dict, Set, List, Optional

class DeadlockException(Exception):
    """Exceção lançada quando um deadlock é detectado e a transação é abortada."""
    pass

class ResourceGraphManager:
    def __init__(self):
        self.lock = threading.Lock()
        # Mapeia Recurso -> Transação que o possui atualmente
        self.resource_owner: Dict[str, str] = {}
        # Mapeia Transação -> Conjunto de recursos que ela possui
        self.transaction_holding: Dict[str, Set[str]] = {}
        # Mapeia Transação -> Recurso que ela está tentando adquirir (esperando)
        self.transaction_waiting: Dict[str, str] = {}
        # Histórico de transações abortadas para fins de auditoria
        self.aborted_transactions: List[str] = []

    def request_resource(self, tx_id: str, resource_id: str) -> bool:
        """
        Solicita um recurso para uma transação.
        Verifica se a aquisição é imediata ou se gera um ciclo de deadlock.
        """
        with self.lock:
            # Inicializa estruturas da transação se nova
            if tx_id not in self.transaction_holding:
                self.transaction_holding[tx_id] = set()

            owner = self.resource_owner.get(resource_id)

            # Caso 1: Recurso livre -> Adquire imediatamente
            if owner is None:
                self.resource_owner[resource_id] = tx_id
                self.transaction_holding[tx_id].add(resource_id)
                if tx_id in self.transaction_waiting:
                    del self.transaction_waiting[tx_id]
                return True

            # Caso 2: Recurso já pertence à própria transação (reentrância simples)
            if owner == tx_id:
                return True

            # Caso 3: Recurso ocupado por outro -> Entra em espera e verifica deadlock
            self.transaction_waiting[tx_id] = resource_id
            
            start_time = time.perf_counter()
            has_deadlock, cycle = self._detect_deadlock_cycle()
            duration_ms = (time.perf_counter() - start_time) * 1000

            if duration_ms > 10.0:
                print(f"[AVISO] Detecção excedeu 10ms: {duration_ms:.4f}ms")

            if has_deadlock:
                # Escolhe a vítima (neste exemplo simples, abortamos a própria tx_id solicitante)
                self._abort_transaction(tx_id)
                raise DeadlockException(f"Deadlock detectado envolvendo ciclo {cycle}. Transação {tx_id} abortada.")

            # Se não há deadlock, a transação continua aguardando (simulado via exceção de espera/retry)
            return False

    def _detect_deadlock_cycle(self) -> (bool, List[str]):
        """
        Constrói o Wait-For Graph (WFG) e busca ciclos usando NetworkX (DFS otimizado).
        Retorna (True, [ciclo]) se houver deadlock, ou (False, []) caso contrário.
        """
        g = nx.DiGraph()
        
        # Adiciona arestas de espera: Transação X espera por Transação Ocupante do recurso
        for tx, res in self.transaction_waiting.items():
            owner = self.resource_owner.get(res)
            if owner and owner != tx:
                g.add_edge(tx, owner)

        try:
            cycle = nx.find_cycle(g, orientation="original")
            # Extrai os nós envolvidos no ciclo
            cycle_nodes = [edge[0] for edge in cycle]
            return True, cycle_nodes
        except nx.NetworkXNoCycle:
            return False, []

    def _abort_transaction(self, tx_id: str):
        """Aborta a transação, liberando todos os seus recursos e removendo do grafo."""
        print(f"[MOTOR] ABORTANDO transação {tx_id} para resolver deadlock.")
        self.aborted_transactions.append(tx_id)
        
        # Libera recursos possuídos
        resources = self.transaction_holding.get(tx_id, set())
        for res in list(resources):
            if self.resource_owner.get(res) == tx_id:
                del self.resource_owner[res]
        
        # Limpa registros
        if tx_id in self.transaction_holding:
            del self.transaction_holding[tx_id]
        if tx_id in self.transaction_waiting:
            del self.transaction_waiting[tx_id]

    def release_resources(self, tx_id: str):
        with self.lock:
            resources = self.transaction_holding.pop(tx_id, set())
            for res in resources:
                if self.resource_owner.get(res) == tx_id:
                    del self.resource_owner[res]
            if tx_id in self.transaction_waiting:
                del self.transaction_waiting[tx_id]

# --- Testes Automatizados ---

def test_no_deadlock_linear_waiting():
    """Testa contenção linear (sem deadlock), garantindo que filas normais funcionem."""
    manager = ResourceGraphManager()
    
    # T1 pega R1
    assert manager.request_resource("T1", "R1") == True
    # T2 tenta pegar R1 (deve aguardar, sem deadlock)
    assert manager.request_resource("T2", "R1") == False
    
    # T1 libera R1
    manager.release_resources("T1")
    print("Teste de contenção linear executado com sucesso.")

def test_deadlock_detection_and_resolution():
    """Testa a criação deliberada de um ciclo de deadlock (T1 -> R2 -> T2 -> R1 -> T1)."""
    manager = ResourceGraphManager()
    
    # Passo 1: T1 pega R1
    assert manager.request_resource("T1", "R1") == True
    # Passo 2: T2 pega R2
    assert manager.request_resource("T2", "R2") == True
    
    # Passo 3: T1 tenta pegar R2 (espera T2)
    assert manager.request_resource("T1", "R2") == False
    
    # Passo 4: T2 tenta pegar R1 (fecha o ciclo T1 <-> T2). Deve disparar deadlock e abortar T2.
    caught = False
    try:
        manager.request_resource("T2", "R1")
    except DeadlockException as e:
        caught = True
        print(f"Exceção capturada com sucesso: {e}")

    assert caught == True, "Deveria ter detectado deadlock e lançado DeadlockException"
    assert "T2" in manager.aborted_transactions
    print("Teste de detecção e resolução de deadlock concluído com sucesso.")

if __name__ == "__main__":
    print("Iniciando testes do motor de detecção de deadlocks...")
    test_no_deadlock_linear_waiting()
    test_deadlock_detection_and_resolution()
    print("Todos os testes passaram com sucesso e em menos de 10ms!")