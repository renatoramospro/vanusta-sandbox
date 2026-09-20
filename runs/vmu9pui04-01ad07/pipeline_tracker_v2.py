import math

class SecurityError(Exception):
    """Exceção para erros de configuração de segurança."""
    pass

class Agent:
    def __init__(self, name, clearance_level):
        self.name = name
        # Fail-Closed: Se o nível não for reconhecido, assume-se o mais alto (CONFIDENTIAL)
        self.clearance_level = clearance_level

class DataArtifact:
    def __init__(self, content, sensitivity, entropy):
        self.content = content
        self.sensitivity = sensitivity
        self.entropy = entropy  # Representa a riqueza de contexto/informação

class PipelineDataFlowTracker:
    HIERARCHY = {'public': 0, 'internal': 1, 'confidential': 2}
    
    def __init__(self):
        self.agents = {}
        self.flows = []
        self.shared_context = {} # Simulação de memória compartilhada

    def register_agent(self, name, clearance_level):
        if clearance_level not in self.HIERARCHY:
            # Fail-Closed: Nível desconhecido é tratado como o mais restritivo
            clearance_level = 'confidential'
        self.agents[name] = Agent(name, clearance_level)

    def add_explicit_flow(self, source, target, artifact):
        self.flows.append((source, target, artifact))

    def update_shared_context(self, key, artifact):
        self.shared_context[key] = artifact

    def _get_level(self, level_str):
        # Fail-Closed: Se houver erro de digitação, retorna nível máximo para segurança
        if level_str not in self.HIERARCHY:
            return self.HIERARCHY['confidential']
        return self.HIERARCHY[level_str]

    def analyze(self):
        alerts = []
        
        # 1. Analisar Fluxos Explícitos (Privacy Leak + Data Loss)
        for src_name, tgt_name, artifact in self.flows:
            target_agent = self.agents[tgt_name]
            
            # Verificação de Privacy Leak (Fail-Closed)
            src_sens_level = self._get_level(artifact.sensitivity)
            tgt_clear_level = self._get_level(target_agent.clearance_level)
            
            if src_sens_level > tgt_clear_level:
                alerts.append({
                    "type": "PRIVACY_LEAK",
                    "msg": f"Vazamento: {src_name} -> {tgt_name} ({artifact.sensitivity} > {target_agent.clearance_level})"
                })

            # Verificação de Data Loss (Integridade)
            # Se o artefato chega com entropia muito baixa para o que se esperava (ex: < 0.1)
            if artifact.entropy < 0.1:
                alerts.append({
                    "type": "DATA_LOSS",
                    "msg": f"Perda de Contexto: Fluxo {src_name} -> {tgt_name} resultou em dados vazios/sanitizados demais."
                })

        # 2. Analisar Dependências Implícitas (Shared Context)
        for key, artifact in self.shared_context.items():
            # Simula que qualquer agente que "leia" o contexto compartilhado deve ser verificado
            # Aqui verificamos se há dados confidenciais no contexto que agentes 'public' poderiam acessar
            for agent_name, agent in self.agents.items():
                if agent.clearance_level == 'public':
                    if self._get_level(artifact.sensitivity) > 0:
                        alerts.append({
                            "type": "IMPLICIT_LEAK",
                            "msg": f"Vazamento Implícito: Agente {agent_name} pode acessar '{key}' no contexto compartilhado."
                        })

        return alerts

def run_experiment():
    tracker = PipelineDataFlowTracker()
    
    # Setup Agentes
    tracker.register_agent("Agente_Analista", "internal")
    tracker.register_agent("Agente_LLM_Publico", "public")
    tracker.register_agent("Agente_Auditor", "confidential")
    tracker.register_agent("Agente_Errado", "nivel_inexistente") # Teste Fail-Closed

    # Cenário 1: Privacy Leak (Explícito)
    data_sensivel = DataArtifact("PII_DATA", "confidential", 0.9)
    tracker.add_explicit_flow("Agente_Analista", "Agente_LLM_Publico", data_sensivel)

    # Cenário 2: Data Loss (Sanitização destrutiva)
    data_vazia = DataArtifact("", "internal", 0.01) # Entropia quase zero
    tracker.add_explicit_flow("Agente_Analista", "Agente_Auditor", data_vazia)

    # Cenário 3: Dependência Implícita (Memória Compartilhada)
    tracker.update_shared_context("session_token", DataArtifact("secret_token", "internal", 0.8))

    # Cenário 4: Teste Fail-Closed (Erro de digitação no registro)
    # Agente_Errado deve ser tratado como 'confidential'
    assert tracker.agents["Agente_Errado"].clearance_level == "confidential"

    alerts = tracker.analyze()
    
    print(f"--- Relatório de Auditoria ---")
    for a in alerts:
        print(f"[{a['type']}] {a['msg']}")

    # Validações
    types_found = [a['type'] for a in alerts]
    assert "PRIVACY_LEAK" in types_found
    assert "DATA_LOSS" in types_found
    assert "IMPLICIT_LEAK" in types_found
    print("\nSUCESSO: Todos os pontos críticos (Privacidade, Integridade e Implícitos) detectados.")

if __name__ == "__main__":
    try:
        run_experiment()
    except Exception as e:
        print(f"FALHA NO EXPERIMENTO: {e}")
        exit(1)