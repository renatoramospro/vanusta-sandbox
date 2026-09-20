import random
from dataclasses import dataclass
from enum import IntEnum

# 1. Definição de Domínios e Atributos
class Sensitivity(IntEnum):
    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    SECRET = 4

@dataclass
class Context:
    id: str
    payload: str
    sensitivity: Sensitivity

@dataclass
class Agent:
    id: str
    role: str
    clearance: Sensitivity

# 2. O Motor de Política (Policy Engine)
class PolicyEngine:
    def __init__(self):
        self.rules = []

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def evaluate(self, agent: Agent, context: Context) -> bool:
        # Se nenhuma regra permitir, o padrão é DENY (Princípio do Menor Privilégio)
        for rule in self.rules:
            if rule(agent, context):
                return True
        return False

# 3. O Orquestrador com Interceptor
class MultiAgentOrchestrator:
    def __init__(self, engine: PolicyEngine):
        self.engine = engine

    def transfer_context(self, agent: Agent, context: Context) -> bool:
        # O Interceptor verifica a política ANTES da transferência
        if self.engine.evaluate(agent, context):
            return True  # Acesso permitido
        return False     # Acesso negado (Bloqueio de vazamento)

# 4. Simulação de Teste
def run_simulation(iterations=1000):
    engine = PolicyEngine()
    
    # Regra de PBAC: O clearance do agente deve ser >= sensibilidade do contexto
    engine.add_rule(lambda a, c: a.clearance >= c.sensitivity)
    
    orchestrator = MultiAgentOrchestrator(engine)
    
    stats = {
        "total": 0,
        "tp": 0, # True Positive: Bloqueou acesso proibido
        "tn": 0, # True Negative: Permitiu acesso permitido
        "fp": 0, # False Positive: Bloqueou acesso que deveria ser permitido
        "fn": 0, # False Negative: Permitiu acesso proibido (VAZAMENTO!)
    }

    # Gerar agentes e contextos para teste
    roles = ["Guest", "Analyst", "Manager", "Admin"]
    clearances = [Sensitivity.PUBLIC, Sensitivity.INTERNAL, Sensitivity.CONFIDENTIAL, Sensitivity.SECRET]
    
    for i in range(iterations):
        agent = Agent(
            id=f"agent_{i}",
            role=random.choice(roles),
            clearance=random.choice(clearances)
        )
        context = Context(
            id=f"ctx_{i}",
            payload="Sensitive Data Content",
            sensitivity=random.choice(list(Sensitivity))
        )

        # Determinar o que DEVERIA acontecer (Ground Truth)
        should_allow = agent.clearance >= context.sensitivity
        
        # Executar a ação no pipeline
        allowed = orchestrator.transfer_context(agent, context)

        # Registrar estatísticas
        stats["total"] += 1
        if should_allow and allowed:
            stats["tn"] += 1
        elif not should_allow and not allowed:
            stats["tp"] += 1
        elif should_allow and not allowed:
            stats["fp"] += 1
        elif not should_allow and allowed:
            stats["fn"] += 1

    return stats

if __name__ == "__main__":
    print("Iniciando simulação de 1.000 execuções de pipeline multi-agente...")
    results = run_simulation(1000)
    
    accuracy = (results["tn"] + results["tp"]) / results["total"] * 100
    fp_rate = (results["fp"] / results["total"]) * 100
    fn_rate = (results["fn"] / results["total"]) * 100
    
    print("-" * 30)
    print(f"RESULTADOS DA SIMULAÇÃO:")
    print(f"Total de execuções: {results['total']}")
    print(f"Acurácia: {accuracy:.2f}%")
    print(f"Taxa de Falsos Positivos (Bloqueios indevidos): {fp_rate:.2f}%")
    print(f"Taxa de Falsos Negativos (Vazamentos de dados): {fn_rate:.2f}%")
    print("-" * 30)

    # Validação dos Critérios de Sucesso
    success = True
    if accuracy < 95:
        print("FALHA: Acurácia abaixo de 95%")
        success = False
    if fp_rate > 1.0:
        print("FALHA: Falsos Positivos acima de 1%")
        success = False
    if fn_rate > 1.0:
        print("FALHA: Falsos Negativos acima de 1%")
        success = False
    if results["fn"] > 0:
        print("FALHA CRÍTICA: Vazamento de dados detectado (Falsos Negativos > 0)!")
        success = False

    if success:
        print("VEREDITO: MISSÃO CUMPRIDA COM SUCESSO")
        exit(0)
    else:
        print("VEREDITO: MISSÃO FALHOU")
        exit(1)