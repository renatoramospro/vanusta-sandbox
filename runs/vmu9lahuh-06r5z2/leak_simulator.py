import json
import re

class MultiAgentPipeline:
    def __init__(self, topology):
        self.topology = topology  # Lista de agentes e suas permissões
        self.trace = []

    def run_step(self, agent_id, input_text, internal_thought, output_text, is_sensitive=False):
        step_data = {
            "agent_id": agent_id,
            "input": input_text,
            "thought": internal_thought,
            "output": output_text,
            "sensitive_data_present": is_sensitive
        }
        self.trace.append(step_data)
        return output_text

def detect_leak(trace, sensitive_pattern):
    """
    Analisa o trace para encontrar se um dado sensível 
    saiu de um agente e apareceu no input de outro.
    """
    leaks = []
    for i in range(len(trace) - 1):
        current_step = trace[i]
        next_step = trace[i+1]
        
        # Verifica se o output do atual contém o padrão sensível
        if re.search(sensitive_pattern, current_step["output"]):
            # Verifica se o próximo agente recebeu esse dado no input
            if re.search(sensitive_pattern, next_step["input"]):
                leaks.append({
                    "type": "PII_LEAK",
                    "from_step": i,
                    "to_step": i + 1,
                    "pattern": sensitive_pattern
                })
    return leaks

# --- EXECUÇÃO DO EXPERIMENTO ---

# 1. Configuração do cenário
PII_PATTERN = r"ID-\d{4}"  # Exemplo: ID-1234
pipeline = MultiAgentPipeline(topology=[{"id": "Orchestrator", "priv": "high"}, {"id": "Worker", "priv": "low"}])

# 2. Simulação de um vazamento (Leak Scenario)
print("--- Cenário 1: Vazamento de PII ---")
# Passo 1: Orquestrador processa dado sensível
pipeline.run_step(
    agent_id="Orchestrator",
    input_text="Processar usuário ID-9999",
    internal_thought="Preciso passar o ID para o worker",
    output_text="Trabalhe com o registro ID-9999", # VAZAMENTO AQUI: O ID está no output
    is_sensitive=True
)

# Passo 2: Worker recebe o output do Orquestrador como input
pipeline.run_step(
    agent_id="Worker",
    input_text="O registro é ID-9999", # O dado vazou para o input do worker
    internal_thought="Vou processar",
    output_text="Concluído"
)

# 3. Simulação de um caso de Context Loss (Não é vazamento)
print("\n--- Cenário 2: Context Loss (Não é vazamento) ---")
pipeline_loss = MultiAgentPipeline(topology=[])
pipeline_loss.run_step("A", "Olá", "Pensando", "Oi")
pipeline_loss.run_step("B", "...", "Pensando", "Tudo bem") # B não recebeu nada do A

# 4. Verificação e Resultados
leaks_found = detect_leak(pipeline.trace, PII_PATTERN)
leaks_loss_found = detect_leak(pipeline_loss.trace, PII_PATTERN)

print(f"\nResultados do Cenário 1 (Esperado: 1 leak): {len(leaks_found)} leak(s) detectado(s).")
for l in leaks_found:
    print(f"  >> Detalhe: {l}")

print(f"Resultados do Cenário 2 (Esperado: 0 leaks): {len(leaks_loss_found)} leak(s) detectado(s).")

# Assertions para garantir que o experimento funciona como esperado
assert len(leaks_found) == 1, "Falha ao detectar vazamento real"
assert len(leaks_loss_found) == 0, "Falso positivo: detectou vazamento onde houve apenas perda de contexto"
print("\n[SUCESSO] O simulador de rotulagem distingue corretamente Leak de Loss.")