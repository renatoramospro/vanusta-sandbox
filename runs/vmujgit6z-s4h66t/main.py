import time
import json
from enum import Enum

class State(Enum):
    INIT = 1
    PREPARING = 2
    COMMITTED = 3
    ABORTED = 4

class Participant:
    def __init__(self, node_id, fail_on_prepare=False):
        self.node_id = node_id
        self.state = State.INIT
        self.fail_on_prepare = fail_on_prepare
        self.data = {"balance": 100}

    def prepare(self, tx_data):
        print(f"[Participante {self.node_id}] Recebeu PREPARE com dados: {tx_data}")
        if self.fail_on_prepare:
            print(f"[Participante {self.node_id}] FALHA simulada na preparação! Votando ABORT.")
            return "VOTE_ABORT"
        
        # Simula validação e escrita em log local
        self.state = State.PREPARING
        return "VOTE_COMMIT"

    def commit(self, decision):
        if decision == "GLOBAL_COMMIT":
            self.state = State.COMMITTED
            print(f"[Participante {self.node_id}] Transação CONFIRMADA (COMMIT).")
        else:
            self.state = State.ABORTED
            print(f"[Participante {self.node_id}] Transação ABORTADA.")

class Coordinator:
    def __init__(self, participants):
        self.participants = participants
        self.state = State.INIT

    def execute_transaction(self, tx_data):
        print(f"\n--- Iniciando Transação 2PC com dados: {tx_data} ---")
        self.state = State.PREPARING

        # Fase 1: Prepare
        votes = []
        for p in self.participants:
            try:
                vote = p.prepare(tx_data)
                votes.append(vote)
            except Exception as e:
                print(f"[Coordenador] Erro ao comunicar com participante {p.node_id}: {e}")
                votes.append("VOTE_ABORT")

        # Decisão do Coordenador
        if all(v == "VOTE_COMMIT" for v in votes):
            decision = "GLOBAL_COMMIT"
            self.state = State.COMMITTED
        else:
            decision = "GLOBAL_ABORT"
            self.state = State.ABORTED

        print(f"[Coordenador] Decisão tomada: {decision}")

        # Fase 2: Commit / Abort
        for p in self.participants:
            p.commit(decision)

        return decision

# Testes automatizados demonstrando o comportamento correto e robusto
if __name__ == "__main__":
    print("=== TESTE 1: Transação Bem-Sucedida ===")
    p1 = Participant(node_id=1)
    p2 = Participant(node_id=2)
    coord = Coordinator([p1, p2])
    result1 = coord.execute_transaction({"amount": 50})
    assert result1 == "GLOBAL_COMMIT", f"Esperado GLOBAL_COMMIT, obtido {result1}"
    assert p1.state == State.COMMITTED
    assert p2.state == State.COMMITTED
    print("Teste 1 passou com sucesso!\n")

    print("=== TESTE 2: Transação Abortada por Falha em Participante ===")
    p3 = Participant(node_id=3, fail_on_prepare=False)
    p4 = Participant(node_id=4, fail_on_prepare=True) # Vai falhar no prepare
    coord2 = Coordinator([p3, p4])
    result2 = coord2.execute_transaction({"amount": 200})
    assert result2 == "GLOBAL_ABORT", f"Esperado GLOBAL_ABORT, obtido {result2}"
    assert p3.state == State.ABORTED
    assert p4.state == State.ABORTED
    print("Teste 2 passou com sucesso!\n")
    
    print("Todos os testes do 2PC executados e validados com código 0!")