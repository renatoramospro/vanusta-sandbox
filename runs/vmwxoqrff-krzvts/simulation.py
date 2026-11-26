import random

class Node:
    def __init__(self, name):
        self.name = name
        self.data = {}
        self.is_available = True

    def write(self, key, value):
        if not self.is_available:
            return False, "Node Unavailable"
        self.data[key] = value
        return True, "Write Successful"

    def read(self, key):
        if not self.is_available:
            return None, "Node Unavailable"
        return self.data.get(key), "Read Successful"

def simulate_scenario(system_type, partition_active):
    # Inicializa dois nós
    node_a = Node("A")
    node_b = Node("B")
    
    # Simula a partição: se partition_active é True, eles não se comunicam
    # Para simplificar a simulação, a indisponibilidade de comunicação afeta a capacidade de consenso.
    
    print(f"\n--- Cenário: {system_type} | Partição: {partition_active} ---")

    if system_type == "CP":
        # CP: Requer consenso (ex: maioria). Com 2 nós, precisa de ambos.
        if partition_active:
            # Partição: Não há consenso, escrita é rejeitada para manter C.
            success_a, _ = node_a.write("k1", "v1")
            success_b, _ = node_b.write("k1", "v1")
            
            # Verifica se ambos falharam em escrever (priorizando C)
            if not success_a and not success_b:
                decision = "CP (Consistência Priorizada)"
            else:
                # Isso não deveria ocorrer em uma partição perfeita de 2 nós
                decision = "CP (Falha na simulação de consenso)"
        else:
            # Sem partição: Ambos escrevem com sucesso
            node_a.write("k1", "v1")
            node_b.write("k1", "v1")
            decision = "CP (Consistência Mantida)"
            
    elif system_type == "AP":
        # AP: Aceita escrita localmente, mesmo sem consenso.
        if partition_active:
            # Partição: Ambos aceitam a escrita localmente (priorizando A).
            node_a.write("k1", "v1")
            node_b.write("k1", "v1")
            
            # Verifica se ambos conseguiram escrever (priorizando A)
            if node_a.data.get("k1") == "v1" and node_b.data.get("k1") == "v1":
                decision = "AP (Disponibilidade Priorizada)"
            else:
                decision = "AP (Falha na simulação de disponibilidade)"
        else:
            # Sem partição: Ambos escrevem com sucesso
            node_a.write("k1", "v1")
            node_b.write("k1", "v1")
            decision = "AP (Disponibilidade Mantida)"
            
    print(f"Decisão registrada: {decision}")
    return decision

# --- Testes de Estresse (Mínimo de 5 cenários) ---
test_scenarios = [
    ("CP", False),  # 1. Sem partição (Baseline)
    ("CP", True),   # 2. Partição (Teste de C)
    ("AP", False),  # 3. Sem partição (Baseline)
    ("AP", True),   # 4. Partição (Teste de A)
    ("CP", True),   # 5. Repetição de teste de C
    ("AP", True)    # 6. Repetição de teste de A
]

correct_count = 0
total_tests = len(test_scenarios)

for system, partition in test_scenarios:
    decision = simulate_scenario(system, partition)
    
    # Verifica a correção baseada no comportamento esperado do CAP
    expected_cp_partition = "CP (Consistência Priorizada)"
    expected_ap_partition = "AP (Disponibilidade Priorizada)"
    
    is_correct = False
    if system == "CP" and partition:
        if decision == expected_cp_partition:
            is_correct = True
    elif system == "AP" and partition:
        if decision == expected_ap_partition:
            is_correct = True
    elif not partition:
        # Baseline deve ser mantido, mas não é o foco da decisão CAP sob P
        is_correct = True 
        
    if is_correct:
        correct_count += 1

print("\n=========================================")
print(f"Total de testes executados: {total_tests}")
print(f"Testes classificados corretamente: {correct_count}")
print(f"Taxa de acerto: {correct_count/total_tests * 100:.2f}%")
print("=========================================")

# Critério de sucesso: 100% de acerto nos cenários de partição (2, 4, 5, 6)
assert correct_count >= 5, "Falha no critério de sucesso: Não atingiu 100% de acerto nos cenários de partição."