import json

class Artifact:
    """Representa o dado trafegando entre agentes."""
    def __init__(self, data, sensitive_keys=None):
        self.data = data
        self.sensitive_keys = sensitive_keys or []

    def __repr__(self):
        return f"Artifact(keys={list(self.data.keys())}, sensitive={self.sensitive_keys})"

class Agent:
    """Representa um agente no pipeline."""
    def __init__(self, name, permission_level, essential_keys=None):
        self.name = name
        self.permission_level = permission_level  # 1: Low, 2: Medium, 3: High
        self.essential_keys = essential_keys or []

    def process(self, artifact: Artifact) -> Artifact:
        # Implementação padrão: apenas passa o dado adiante
        return artifact

class DependencyMapper:
    """Algoritmo de mapeamento para detectar pontos críticos."""
    def __init__(self):
        self.critical_points = []

    def analyze_transition(self, source: Agent, target: Agent, artifact_out: Artifact):
        """Analisa a transição de dados de um agente para outro."""
        # 1. Detecção de Perda (Data Loss)
        # Se o target recebeu menos chaves essenciais do que o source enviou
        missing_essential = [k for k in source.essential_keys if k not in artifact_out.data]
        if missing_essential:
            self.critical_points.append({
                "type": "DATA_LOSS",
                "agents": (source.name, target.name),
                "details": f"Missing essential keys: {missing_essential}"
            })

        # 2. Detecção de Vazamento (Privacy Leak)
        # Se o target possui chaves sensíveis mas seu nível de permissão é baixo
        for key in artifact_out.sensitive_keys:
            if key in artifact_out.data and target.permission_level < 3:
                self.critical_points.append({
                    "type": "PRIVACY_LEAK",
                    "agents": (source.name, target.name),
                    "details": f"Sensitive key '{key}' leaked to low-permission agent '{target.name}'"
                })

def simple_schema_validator(artifact: Artifact):
    """
    EQUÍVOCO COMUM: Um validador que apenas checa se o dado é um dicionário.
    Este validador falha em detectar vazamentos de conteúdo sensível.
    """
    return isinstance(artifact.data, dict)

def run_experiment():
    print("--- Iniciando Experimento de Mapeamento de Dependências ---\n")

    # Configuração do Pipeline: Ingestor (High) -> Processor (Med) -> Reporter (Low)
    ingestor = Agent("Ingestor", permission_level=3, essential_keys=["user_id", "email", "ssn"])
    processor = Agent("Processor", permission_level=2, essential_keys=["user_id", "email"])
    reporter = Agent("Reporter", permission_level=1, essential_keys=["user_id"])

    mapper = DependencyMapper()

    # CENÁRIO 1: Fluxo Saudável
    print("[Cenário 1] Fluxo Saudável...")
    data_1 = Artifact({"user_id": 1, "email": "a@b.com", "ssn": "123-45"}, sensitive_keys=["ssn"])
    # Ingestor processa e passa para Processor (Processor deve limpar o SSN)
    # Mas vamos simular um erro: o Processor NÃO limpa o SSN (Vazamento)
    
    # Simulação de erro de processamento no Processor
    # O Processor deveria remover 'ssn', mas ele falha e o repassa.
    artifact_from_ingestor = data_1 
    
    # Transição 1: Ingestor -> Processor
    # O Processor tem permissão 2, mas o SSN exige 3.
    mapper.analyze_transition(ingestor, processor, artifact_from_ingestor)

    # Transição 2: Processor -> Reporter
    # O Reporter tem permissão 1.
    artifact_from_processor = artifact_from_ingestor # Erro: SSN ainda está aqui
    mapper.analyze_transition(processor, reporter, artifact_from_processor)

    # Verificação do Equívoco Comum
    print(f"Validador de Esquema Simples detectou erro? {simple_schema_validator(artifact_from_processor) == False}")
    print(f"Validador de Esquema Simples detectou vazamento? 'Não (ele só checa se é dict)'")

    # Verificação do Nosso Algoritmo
    print(f"\nPontos Críticos Detectados pelo DependencyMapper: {len(mapper.critical_points)}")
    for cp in mapper.critical_points:
        print(f"  - [{cp['type']}] entre {cp['agents']}: {cp['details']}")

    # Validação de Sucesso do Experimento
    # Esperamos detectar ao menos o vazamento de SSN
    leaks = [cp for cp in mapper.critical_points if cp['type'] == "PRIVACY_LEAK"]
    assert len(leaks) > 0, "Falha: O algoritmo não detectou o vazamento de privacidade!"
    
    print("\n[RESULTADO] Experimento concluído com sucesso. Vazamentos identificados.")

if __name__ == "__main__":
    run_experiment()