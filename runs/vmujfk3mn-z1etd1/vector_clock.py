class VectorClock:
    def __init__(self, node_id: str, nodes: list):
        self.node_id = node_id
        self.clock = {n: 0 for n in nodes}

    def increment(self):
        """Incrementa o relógio próprio do nó."""
        if self.node_id in self.clock:
            self.clock[self.node_id] += 1
        return self

    def send_message(self) -> dict:
        """Incrementa o relógio local e retorna uma cópia para envio."""
        self.increment()
        return dict(self.clock)

    def receive_message(self, other_clock: dict):
        """Atualiza o relógio local ao receber uma mensagem de outro nó."""
        for n in self.clock:
            self.clock[n] = max(self.clock[n], other_clock.get(n, 0))
        self.increment()

    def compare(self, other: 'VectorClock') -> str:
        """
        Compara dois relógios vetoriais.
        Retorna:
          '<'  se self precede other (causalidade)
          '>'  se self sucede other
          '==' se são idênticos
          '||' se são concorrentes (paralelos)
        """
        other_dict = other.clock if isinstance(other, VectorClock) else other
        
        self_keys = set(self.clock.keys())
        other_keys = set(other_dict.keys())
        all_keys = self_keys.union(other_keys)

        less_or_equal = True
        greater_or_equal = True
        strictly_less = False
        strictly_greater = False

        for k in all_keys:
            v_self = self.clock.get(k, 0)
            v_other = other_dict.get(k, 0)

            if v_self > v_other:
                less_or_equal = False
                strictly_greater = True
            elif v_self < v_other:
                greater_or_equal = False
                strictly_less = True

        if self.clock == other_dict:
            return '=='
        elif less_or_equal and strictly_less:
            return '<'
        elif greater_or_equal and strictly_greater:
            return '>'
        else:
            return '||'

    def __repr__(self):
        return f"VC({self.node_id}: {dict(sorted(self.clock.items()))})"


# --- SIMULAÇÃO COM 5 NÓS DISTRIBUÍDOS ---
def run_simulation():
    print("=== INICIANDO SIMULAÇÃO COM 5 NÓS DISTRIBUÍDOS ===")
    nodes_ids = ['A', 'B', 'C', 'D', 'E']
    
    # Inicializa relógios para os 5 nós
    nodes = {nid: VectorClock(nid, nodes_ids) for nid in nodes_ids}

    # Evento 1: Nó A executa uma ação local
    nodes['A'].increment()
    print(f"Evento A1: {nodes['A']}")

    # Evento 2: Nó A envia mensagem para o Nó B
    msg_A_B = nodes['A'].send_message()
    print(f"Mensagem enviada de A para B: {msg_A_B}")

    # Nó B recebe a mensagem de A
    nodes['B'].receive_message(msg_A_B)
    print(f"Evento B1 (recebeu de A): {nodes['B']}")

    # Evento 3 (Concorrência): Enquanto B processa A, o Nó C age de forma totalmente independente
    nodes['C'].increment()
    nodes['C'].increment()
    print(f"Evento C1 (Independente): {nodes['C']}")

    # Validação de Causalidade (A precede B)
    rel_AB = nodes['A'].compare(nodes['B'])
    print(f"Comparação A vs B -> Esperado '<': {rel_AB}")
    assert rel_AB == '<', f"Erro de causalidade: A deveria preceder B, mas deu {rel_AB}"

    # Validação de Concorrência (B e C são concorrentes)
    rel_BC = nodes['B'].compare(nodes['C'])
    print(f"Comparação B vs C -> Esperado '||' (concorrentes): {rel_BC}")
    assert rel_BC == '||', f"Erro de concorrência: B e C deveriam ser concorrentes, mas deu {rel_BC}"

    # Simulação estendida envolvendo 5 nós (A, B, C, D, E)
    print("\n--- Cascata de mensagens entre os 5 nós ---")
    msg_B = nodes['B'].send_message()
    nodes['D'].receive_message(msg_B)
    
    msg_D = nodes['D'].send_message()
    nodes['E'].receive_message(msg_D)
    
    print(f"Nó D final: {nodes['D']}")
    print(f"Nó E final: {nodes['E']}")

    # Verificar que A precede E transitivamente
    rel_AE = nodes['A'].compare(nodes['E'])
    print(f"Comparação A vs E (transitiva) -> Esperado '<': {rel_AE}")
    assert rel_AE == '<', "Erro na transitividade causal entre A e E"

    print("\n[SUCESSO] Todos os testes de 5 nós, causalidade e concorrência passaram!")

if __name__ == "__main__":
    run_simulation()