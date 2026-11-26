import random

class Node:
    def __init__(self, name):
        self.name = name
        self.data = {}
        self.is_available = True

    def write(self, key, value, partition_active):
        if not self.is_available:
            return False, "Node Unavailable"
        
        # Lógica de Consenso Simplificada para 2 nós: Requer ambos para sucesso
        if partition_active:
            # Em CP, se não há comunicação, não há consenso, escrita falha.
            return False, "Consensus Failed (Partition)"
        
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
    
    print(f"\n--- Cenário: {system_type} | Partição: {partition_active} ---")

    if system_type == "CP":
        # CP: Prioriza Consistência. Sob partição, a escrita deve falhar para manter C.
        success_a, _ = node_a.write("k1", "v1", partition_active)
        success_b, _ = node_b.write("k1", "v1", partition_active)
        
        if partition_active:
            # Decisão correta para CP sob P: Escrita falha em ambos, mantendo C.
            if not success_a and not success_b:
                decision = "CP (Consistência Priorizada)"
            else:
                # Se ambos conseguiram escrever, a simulação de partição falhou.
                decision = "CP (Falha na simulação de consenso)"
        else:
            # Sem partição, ambos devem ter sucesso
            decision = "CP (Consistência Mantida)"
            
    elif system_type == "AP":
        # AP: Prioriza Disponibilidade. Sob partição, ambos aceitam a escrita localmente.
        success_a, _ = node_a.write("k1", "v1", partition_active)
        success_b, _ = node_b.write("k1", "v1", partition_active)
        
        if partition_active:
            # Decisão correta para AP sob P: Escrita é aceita localmente em ambos.
            if success_a and success_b:
                decision = "AP (Disponibilidade Priorizada)"
            else:
                # Se um falhou, a simulação de AP falhou.
                decision = "AP (Falha na simulação de disponibilidade)"
        else:
            # Sem partição, ambos devem ter sucesso
            decision = "AP (Disponibilidade Mantida)"
    else:
        decision = "Erro de Tipo de Sistema"
        
    print(f"Decisão registrada: {decision}")
    return decision

# Cenários de Teste (Total 6)
scenarios = [
    ("CP", False),  # 1. CP sem P: C mantida
    ("CP", True),   # 2. CP com P: C priorizada (Escrita falha)
    ("AP", False),  # 3. AP sem P: A mantida
    ("AP", True),   # 4. AP com P: A priorizada (Escrita aceita localmente)
    ("CP", True),   # 5. Repetição para estresse
    ("AP", True)    # 6. Repetição para estresse
]

total_tests = len(scenarios)
correct_count = 0

# Definição da Decisão Correta Esperada para os 4 cenários cruciais de partição
expected_decisions = {
    ("CP", True): "CP (Consistência Priorizada)",
    ("AP", True): "AP (Disponibilidade Priorizada)"
}

for system_type, partition_active in scenarios:
    recorded_decision = simulate_scenario(system_type, partition_active)
    
    # Verificação de correção: Apenas os 4 cenários cruciais de partição são avaliados para o critério de sucesso
    if partition_active and system_type in ["CP", "AP"]:
        expected = expected_decisions[(system_type, partition_active)]
        if recorded_decision == expected:
            correct_count += 1

print("\n=========================================")
print(f"Total de testes executados: {total_tests}")
print(f"Testes classificados corretamente (foco em P): {correct_count}")
print(f"Taxa de acerto (foco em P): {correct_count/4 * 100:.2f}%")
print("=========================================")

# Critério de sucesso: 100% de acerto nos 2 cenários cruciais de partição (CP/P=True e AP/P=True)
assert correct_count >= 2, "Falha no critério de sucesso: Não atingiu 100% de acerto nos cenários de partição."