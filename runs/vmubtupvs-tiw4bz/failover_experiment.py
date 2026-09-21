import time
import json
from typing import Dict, Any, List, Optional

class ExternalSystemRegistry:
    """Simula um registro distribuído externo (ex: DB/Redis) para checagem absoluta de idempotência."""
    def __init__(self):
        self.completed_actions: List[str] = []

    def is_completed(self, action_id: str) -> bool:
        return action_id in self.completed_actions

    def register(self, action_id: str):
        if action_id not in self.completed_actions:
            self.completed_actions.append(action_id)

class AgentNode:
    """Representa um Agente Vanusta na rede de orquestração com suporte a falhas e contexto."""
    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.status = "HEALTHY" # HEALTHY, UNRESPONSIVE, DEAD
        self.last_heartbeat = time.time()
        self.context_state: Dict[str, Any] = {"history": [], "processed_actions": []}

    def heartbeat(self):
        self.last_heartbeat = time.time()

    def execute_task(self, task: str, action_id: str, registry: ExternalSystemRegistry) -> str:
        # Simula falha em cascata intencional se configurado para testes
        if getattr(self, "simulate_instant_crash", False):
            self.status = "DEAD"
            raise RuntimeError(f"[{self.agent_id}] Crash catastrófico imediato pós-assunção da tarefa!")

        # 1. Checagem no registro externo (previne dessincronia in-flight)
        if registry.is_completed(action_id):
            return f"[{self.agent_id}] Ação {action_id} já consta no registro externo. Ignorando duplicação."

        # 2. Checagem no contexto local copiado
        if action_id in self.context_state.get("processed_actions", []):
            return f"[{self.agent_id}] Ação {action_id} já executada (contexto local). Idempotência garantida."

        # Execução bem sucedida da ação externa
        registry.register(action_id)
        self.context_state["history"].append({"task": task, "status": "executed"})
        self.context_state["processed_actions"].append(action_id)
        return f"[{self.agent_id}] Tarefa executada com sucesso: {task} (Ação ID: {action_id})"


class Supervisor:
    """Orquestrador central com suporte a failover em cascata e verificação externa."""
    def __init__(self, agents: List[AgentNode], registry: ExternalSystemRegistry):
        self.agents = agents
        self.registry = registry
        self.timeout_threshold = 2.0

    def check_health(self) -> List[str]:
        current_time = time.time()
        failed_agents = []
        for agent in self.agents:
            if agent.status == "HEALTHY" and (current_time - agent.last_heartbeat) > self.timeout_threshold:
                agent.status = "DEAD"
                failed_agents.append(agent.agent_id)
        return failed_agents

    def execute_failover_cascade(self, failed_agent_id: str, task: str, action_id: str, capability: str) -> str:
        print(f"\n[SUPORTE/ALERTA] Falha detectada no agente: {failed_agent_id}. Iniciando failover em cascata...")
        
        # Localiza o agente falho para extrair o último contexto cognitivo conhecido
        failed_agent = next((a for a in self.agents if a.agent_id == failed_agent_id), None)
        cognitive_state = failed_agent.context_state.copy() if failed_agent else {"history": [], "processed_actions": []}
        print(f"[CONTEXTO] Estado cognitivo extraído: {len(cognitive_state['processed_actions'])} ações processadas.")

        # Busca candidatos saudáveis que possuem a capacidade exigida
        candidates = [a for a in self.agents if a.status == "HEALTHY" and capability in a.capabilities]

        if not candidates:
            return "[FALHA CRÍTICA] Nenhum agente saudável disponível na frota para failover!"

        # Tenta iterativamente cada candidato (Tratamento de Falhas em Cascata)
        for candidate in candidates:
            print(f"[TENTATIVA DE REDIRECIONAMENTO] Designando agente substituto: {candidate.agent_id}")
            # Injeta o contexto cognitivo
            candidate.context_state = cognitive_state.copy()
            
            try:
                # Tenta executar a tarefa no agente substituto
                result = candidate.execute_task(task, action_id, self.registry)
                print(f"[SUCESSO] Tarefa assumida por {candidate.agent_id}")
                return result
            except Exception as e:
                print(f"[FALHA EM CASCATA] Agente substituto {candidate.agent_id} falhou ao assumir: {e}")
                candidate.status = "DEAD"
                # Continua o loop para o próximo candidato saudável disponível

        return "[FALHA CRÍTICA] Todos os candidatos da cascata falharam!"


# --- BLOCO DE EXECUÇÃO DO EXPERIMENTO ---
if __name__ == "__main__":
    print("=== INICIANDO EXPERIMENTO DE FAILOVER VANUSTA (ROBUSTO: CASCATA & DESSINCRONIA) ===")
    
    registry = ExternalSystemRegistry()
    
    # Frota de Agentes: Alpha (vai cair), Beta 1 (vai falhar em cascata), Beta 2 (saudável definitivo)
    alpha = AgentNode("Agent-Alpha", ["data_processing"])
    beta1 = AgentNode("Agent-Beta-1", ["data_processing"])
    beta2 = AgentNode("Agent-Beta-2", ["data_processing"])
    
    # Configura Beta 1 para falhar imediatamente ao tentar assumir (simulando falha em cascata)
    beta1.simulate_instant_crash = True

    agents = [alpha, beta1, beta2]
    supervisor = Supervisor(agents, registry)

    # --- Fase 1: Operação Normal e Cenário de Borda (In-flight action) ---
    print("\n--- Fase 1: Operação Normal ---")
    # Simula cenário de borda: a ação externa foi disparada e registrada no registro externo,
    # mas o Agent-Alpha caiu ANTES de atualizar o seu próprio `context_state` local.
    registry.register("act_inflight_001")
    print("[Agent-Alpha] Disparou ação externa 'act_inflight_001' mas sofreu crash imediato antes de atualizar o log local.")

    # --- Fase 2: Simulação de Queda do Alpha e Detecção ---
    alpha.last_heartbeat = time.time() - 3.0 # Expira heartbeat
    failed_detected = supervisor.check_health()
    print(f"Agentes declarados mortos pelo supervisor: {failed_detected}")
    assert "Agent-Alpha" in failed_detected, "Falha na detecção do Agent-Alpha!"

    # --- Fase 3: Execução do Failover com Cascata e Verificação Externa ---
    print("\n--- Fase 3: Failover com Cascata e Proteção contra Dessincronia ---")
    
    failover_result = supervisor.execute_failover_cascade(
        failed_agent_id="Agent-Alpha",
        task="Continuar processamento pós-queda",
        action_id="act_inflight_001", # ID que estava in-flight
        capability="data_processing"
    )
    print(f"Resultado final do failover: {failover_result}")

    # Validações rigorosas
    assert "já consta no registro externo" in failover_result, "O sistema falhou em detectar a ação in-flight via registro externo e duplicou a transação!"
    assert beta1.status == "DEAD", "O agente em cascata que falhou não foi corretamente isolado!"
    assert beta2.status == "HEALTHY", "O agente final saudável foi indevidamente afetado!"

    print("\n[OK] Experimento aprimorado concluído com sucesso: Falhas em cascata tratadas e dessincronia prevenida!")