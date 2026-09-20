import json

class Agent:
    def __init__(self, name, clearance_level):
        self.name = name
        self.clearance_level = clearance_level  # ex: 'public', 'internal', 'confidential'

class PipelineDataFlowTracker:
    def __init__(self):
        self.agents = {}
        self.edges = [] # (source, target, data_sensitivity)

    def register_agent(self, name, clearance_level):
        self.agents[name] = Agent(name, clearance_level)

    def add_flow(self, source, target, data_sensitivity):
        if source not in self.agents or target not in self.agents:
            raise ValueError("Agente não registrado.")
        self.edges.append((source, target, data_sensitivity))

    def detect_critical_leaks(self):
        """
        Identifica pontos críticos onde dados com sensibilidade maior que 
        o nível de permissão (clearance) do agente receptor são fluídos.
        Hierarquia: public (0) < internal (1) < confidential (2)
        """
        hierarchy = {'public': 0, 'internal': 1, 'confidential': 2}
        leaks = []

        for source, target, sensitivity in self.edges:
            target_agent = self.agents[target]
            source_sensitivity_level = hierarchy.get(sensitivity, 0)
            target_clearance_level = hierarchy.get(target_agent.clearance_level, 0)

            # Ponto crítico: O dado é mais sensível do que o nível de permissão do agente receptor
            if source_sensitivity_level > target_clearance_level:
                leaks.append({
                    "source": source,
                    "target": target,
                    "sensitivity": sensitivity,
                    "target_clearance": target_agent.clearance_level,
                    "severity": "CRITICAL"
                })
        return leaks

# --- Experimento e Validação ---
def run_experiment():
    tracker = PipelineDataFlowTracker()

    # Registrando agentes com diferentes níveis de acesso
    tracker.register_agent("AgenteColetaPublica", "public")
    tracker.register_agent("AgenteProcessamentoInterno", "internal")
    tracker.register_agent("AgenteLLMExterno", "public")  # Vulnerável a vazamento!
    tracker.register_agent("AgenteAuditoriaSegura", "confidential")

    # Definindo fluxos de dados no pipeline
    tracker.add_flow("AgenteColetaPublica", "AgenteProcessamentoInterno", "internal")
    tracker.add_flow("AgenteProcessamentoInterno", "AgenteLLMExterno", "confidential")  # Vazamento aqui!
    tracker.add_flow("AgenteProcessamentoInterno", "AgenteAuditoriaSegura", "confidential")

    leaks = tracker.detect_critical_leaks()
    print(f"Total de pontos críticos detectados: {len(leaks)}")
    for leak in leaks:
        print(f"ALERTA: Fluxo de '{leak['source']}' para '{leak['target']}' "
              f"com dados '{leak['sensitivity']}' excede o clearance '{leak['target_clearance']}'!")

    assert len(leaks) == 1, "Deveria ter encontrado exatamente 1 ponto crítico de vazamento."
    print("Experimento executado com sucesso e asserções validadas!")

if __name__ == "__main__":
    try:
        run_experiment()
    except Exception as e:
        print(f"FALHA NO EXPERIMENTO: {e}")
        exit(1)