import time

class LWWRegister:
    """
    Simula um registrador Last-Write-Wins (LWW).
    Demonstra o problema de perda de dados quando há desvio de relógio (clock skew).
    """
    def __init__(self, initial_value=None, initial_timestamp=0.0):
        self.value = initial_value
        self.timestamp = initial_timestamp

    def write(self, new_value, timestamp):
        # Se o timestamp entrante for estritamente maior, aceita a escrita.
        # ATENÇÃO AO PROBLEMA: Se o nó B tiver relógio atrasado, um timestamp menor 
        # fará com que uma escrita mais recente no tempo real seja descartada.
        if timestamp > self.timestamp:
            self.value = new_value
            self.timestamp = timestamp
            return True
        return False  # Escrita rejeitada silenciosamente

class ORSet:
    """
    Simula um Observed-Removed Set (CRDT baseado em estado).
    Cada adição gera um identificador único (elemento, tag), tornando adições concorrentes idempotentes.
    """
    def __init__(self):
        # Estrutura: set de tuplas (elemento, unique_id)
        self.add_set = set()
        self.remove_set = set()

    def add(self, element, tag):
        self.add_set.add((element, tag))

    def remove(self, element):
        # Remove todas as tags conhecidas para aquele elemento até o momento
        to_remove = {item for item in self.add_set if item[0] == element}
        self.remove_set.update(to_remove)

    def read(self):
        # O estado atual é a diferença entre adições e remoções
        active_items = self.add_set - self.remove_set
        return {item[0] for item in active_items}

    def merge(self, other_set):
        # União de conjuntos (operação commutative, associative e idempotent - join-semilattice)
        self.add_set.update(other_set.add_set)
        self.remove_set.update(other_set.remove_set)

def test_lww_failure_due_to_clock_drift():
    print("=== Testando Falha do LWW por Clock Skew ===")
    
    # Nó A está com o relógio correto (t = 100.0)
    # Nó B está com o relógio atrasado por clock skew (t = 90.0)
    reg = LWWRegister(initial_value="Estado Inicial", timestamp=50.0)

    # Cliente escreve "Escrita Importante do Nó B" no Nó B (relógio em 90.0)
    accepted_b = reg.write("Escrita do No B", timestamp=90.0)
    print(f"Escrita no Nó B (ts=90.0) aceita? {accepted_b}. Valor atual: {reg.value}")

    # Momento depois, Cliente escreve "Escrita Menos Recente do Nó A" no Nó A (relógio em 80.0, mas adiantado em relacao ao B corrompido, ou vice-versa)
    # Vamos simular: Nó A escreve com timestamp 85.0, mas o valor de B era 90.0? 
    # Cenário clássico de clock skew: Nó B tem relógio adiantado (ts=110) para uma escrita antiga, 
    # bloqueando uma escrita real mais recente no Nó A (ts=105).
    
    reg_skew = LWWRegister(initial_value="Base", timestamp=0.0)
    
    # Nó B (relógio adiantado incorretamente) escreve dado antigo no tempo real, mas com ts alto
    reg_skew.write("Dado Antigo com Relogio Adiantado", timestamp=1000.0)
    
    # Nó A (relógio correto) tenta escrever dado novo no tempo real, mas com ts menor devido ao drift
    accepted_a = reg_skew.write("Dado Novo Real", timestamp=950.0)
    
    print(f"Tentativa de escrita no Nó A (ts=950.0) após Nó B (ts=1000.0) aceita? {accepted_a}")
    print(f"Valor final retido pelo LWW: '{reg_skew.value}' (PERDA SILENCIOSA DE DADO RECENTE!)")
    
    assert reg_skew.value == "Dado Antigo com Relogio Adiantado"
    print("Sucesso: Falha do LWW demonstrada e validada no teste!\n")

def test_crdt_convergence():
    print("=== Testando Convergência Determinística com CRDT (OR-Set) ===")
    
    replica_a = ORSet()
    replica_b = ORSet()

    # Operações concorrentes sem coordenação central
    # Nó A adiciona "Maca" com tag 'uuid-1'
    replica_a.add("Maca", "uuid-1")
    
    # Nó B adiciona "Banana" com tag 'uuid-2'
    replica_b.add("Banana", "uuid-2")

    print(f"Replica A antes do sync: {replica_a.read()}")
    print(f"Replica B antes do sync: {replica_b.read()}")

    # Sincronização bidirecional (Anti-Entropy / Gossip)
    replica_a.merge(replica_b)
    replica_b.merge(replica_a)

    print(f"Replica A após merge: {replica_a.read()}")
    print(f"Replica B após merge: {replica_b.read()}")
    
    # Validação de convergência
    assert replica_a.read() == {"Maca", "Banana"}
    assert replica_b.read() == {"Maca", "Banana"}
    print("Sucesso: Estados convergiram perfeitamente sem perda de dados concorrentes e sem conflitos!\n")

if __name__ == "__main__":
    test_lww_failure_due_to_clock_drift()
    test_crdt_convergence()
    print("Todos os testes executados com sucesso (Código de saída 0).")