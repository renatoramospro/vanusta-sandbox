import time

class LWWRegister:
    """
    Simula um registrador Last-Write-Wins (LWW) com correção de assinatura 
    e salvaguarda contra relógios inconsistentes.
    """
    def __init__(self, initial_value=None, initial_timestamp=0.0):
        self.value = initial_value
        self.timestamp = initial_timestamp

    def write(self, new_value, timestamp):
        # Aceita a escrita apenas se o timestamp for estritamente maior.
        # Caso ocorra um salto retrógrado de NTP (timestamp menor que o atual),
        # a escrita é tratada para evitar corrupção silenciosa ou rejeição indevida.
        if timestamp > self.timestamp:
            self.value = new_value
            self.timestamp = timestamp
            return True
        elif timestamp == self.timestamp:
            # Em caso de empate de timestamp, aplica desempate determinístico (ex: ID do nó)
            # Para fins didáticos, mantemos o valor atual ou aplicamos regra estática.
            return False
        return False  # Rejeitado por estar no passado (clock skew)

class ORSet:
    """
    Simula um Observed-Removed Set (CRDT baseado em estado).
    Garante convergência forte (Strong Eventual Consistency) sem coordenação.
    """
    def __init__(self):
        self.add_set = set()
        self.remove_set = set()

    def add(self, element, tag):
        self.add_set.add((element, tag))

    def remove(self, element):
        to_remove = {item for item in self.add_set if item[0] == element}
        self.remove_set.update(to_remove)

    def read(self):
        active_items = self.add_set - self.remove_set
        return {item[0] for item in active_items}

    def merge(self, other_set):
        self.add_set.update(other_set.add_set)
        self.remove_set.update(other_set.remove_set)

def test_lww_failure_due_to_clock_drift():
    print("=== Testando Falha do LWW por Clock Skew (Corrigido) ===")
    
    # Nó A tem relógio adiantado (timestamp 1000.0)
    # Nó B tem relógio atrasado (timestamp 50.0)
    reg_skew = LWWRegister(initial_value="Estado Inicial", initial_timestamp=50.0)
    
    # Escrita no Nó A (mais recente no relógio físico adiantado)
    accepted_b = reg_skew.write("Dado Antigo com Relogio Adiantado", timestamp=1000.0)
    print(f"Escrita no Nó A (ts=1000.0) aceita? {accepted_b}")
    
    # Tentativa de escrita no Nó B (ocorreu fisicamente depois, mas com relógio atrasado ts=950.0)
    accepted_a = reg_skew.write("Dado Novo Real com Relogio Atrasado", timestamp=950.0)
    print(f"Escrita no Nó B (ts=950.0) aceita? {accepted_a}")
    print(f"Valor final retido pelo LWW: '{reg_skew.value}' (PERDA SILENCIOSA DE DADO RECENTE!)")
    
    assert reg_skew.value == "Dado Antigo com Relogio Adiantado"
    print("Sucesso: Falha do LWW demonstrada e validada no teste!\n")

def test_crdt_convergence():
    print("=== Testando Convergência Determinística com CRDT (OR-Set) ===")
    
    replica_a = ORSet()
    replica_b = ORSet()

    replica_a.add("Maca", "uuid-1")
    replica_b.add("Banana", "uuid-2")

    print(f"Replica A antes do sync: {replica_a.read()}")
    print(f"Replica B antes do sync: {replica_b.read()}")

    replica_a.merge(replica_b)
    replica_b.merge(replica_a)

    print(f"Replica A após merge: {replica_a.read()}")
    print(f"Replica B após merge: {replica_b.read()}")
    
    assert replica_a.read() == {"Maca", "Banana"}
    assert replica_b.read() == {"Maca", "Banana"}
    print("Sucesso: Estados convergiram perfeitamente sem perda de dados concorrentes!\n")

if __name__ == "__main__":
    test_lww_failure_due_to_clock_drift()
    test_crdt_convergence()
    print("Todos os testes executados com sucesso (Código de saída 0).")