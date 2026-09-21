import time
import json
from typing import Dict, Any, List, Optional

class AgentNode:
    """Representa um Agente Vanusta na rede de orquestração."""
    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.status = "HEALTHY" # HEALTHY, UNRESPONSIVE, DEAD
        self.last_heartbeat = time.time()
        self.context_state: Dict[str, Any] = {"history": [], "last_action_id": None}
        self.action_log: List[str] = [] # Simula ações externas executadas (para idempotência)

    def heartbeat(self):
        self.last_heartbeat = time.time()

    def execute_task(self, task: str, action_id: str) -> str:
        # Verifica idempotência: se a ação externa já foi registrada, não repete.
        processed_actions = self.context_state.get("processed_actions", [])
        if action_id in processed_actions:
            return f"[{self.agent_id}] Ação {action_id} já executada anteriormente. Ignorando repetição (Idempotência garantida)."
        
        # Execução normal
        self.context_state["history"].append({"task": task, "status": "executed"})
        if "processed_actions" not in self.context_state:
            self.context_state["processed_actions"] = []
        self.context_state["processed_actions"].append(action_id)
        self.action_log.append(action_id)
        return f"[{self.agent_id}] Tarefa executada com sucesso: {task} (Ação ID: {action_id})"

class VanustaSupervisor:
    """Supervisor responsável por monitorar, detectar falhas e realizar failover automático."""
    def __init__(self, heartbeat_timeout: float = 2.0):
        self.agents: Dict[str, AgentNode] = {}
        self.heartbeat_timeout = heartbeat_timeout

    def register_agent(self, agent: AgentNode):
        self.agents[agent.agent_id] = agent

    def check_health(self) -> List[str]:
        """Detecta agentes com falha baseada em timeout de heartbeat."""
        current_time = time.time()
        failed_agents = []
        for agent_id, agent in self.agents.items():
            if agent.status == "HEALTHY" and (current_time - agent.last_heartbeat) > self.heartbeat_timeout:
                agent.status = "DEAD"
                failed_agents.append(agent_id)
        return failed_agents

    def execute_failover(self, failed_agent_id: str, task: str, action_id: str, capability: str) -> str:
        print(f"\n[SUPORTE/ALERTA] Falha detectada no agente: {failed_agent_id}. Iniciando failover automático...")
        
        failed_agent = self.agents.get(failed_agent_id)
        if not failed_agent:
            return "[FALHA] Agente falho não encontrado no registro do supervisor."

        # 1. Extração do Estado Cognitivo (Contexto) do agente falho
        cognitive_context = failed_agent.context_state.copy()
        print(f"[CONTEXTO] Estado cognitivo extraído de {failed_agent_id}: {len(cognitive_context.get('history', []))} passos no histórico.")

        # 2. Seleção de Agente Saudável Alternativo baseado em Capacidade
        healthy_substitute: Optional[AgentNode] = None
        for agent_id, agent in self.agents.items():
            if agent.status == "HEALTHY" and capability in agent.capabilities:
                healthy_substitute = agent
                break

        if not healthy_substitute:
            return "[FALHA] Nenhum agente saudável disponível com a capacidade exigida!"

        print(f"[REDIRECIONAMENTO] Agente saudável selecionado para assumir a tarefa: {healthy_substitute.agent_id}")

        # 3. Transferência de Estado Cognitivo para o novo agente
        healthy_substitute.context_state = cognitive_context
        print(f"[INJEÇÃO] Contexto cognitivo injetado com sucesso em {healthy_substitute.agent_id}.")

        # 4. Execução da tarefa no novo agente com validação de idempotência
        result = healthy_substitute.execute_task(task, action_id)
        return result

if __name__ == "__main__":
    print("=== INICIANDO EXPERIMENTO DE FAILOVER AUTOMÁTICO VANUSTA (VERSÃO CORRIGIDA) ===")

    # Configuração do Supervisor e Agentes
    supervisor = VanustaSupervisor(heartbeat_timeout=1.0)
    
    alpha = AgentNode("Agent-Alpha", capabilities=["data_processing"])
    beta = AgentNode("Agent-Beta", capabilities=["data_processing"])
    
    supervisor.register_agent(alpha)
    supervisor.register_agent(beta)

    # --- Fase 1: Operação Normal ---
    print("\n--- Fase 1: Operação Normal ---")
    alpha.heartbeat()
    initial_result = alpha.execute_task("Processar lote de dados A", action_id="act_001")
    print(initial_result)

    # --- Fase 2: Simulação de Queda do Agente Alpha (Mantendo Beta Saudável) ---
    print("\n--- Fase 2: Simulação de Queda do Agente Alpha ---")
    # Forçamos o tempo de último heartbeat de Alpha para expirar
    alpha.last_heartbeat = time.time() - 3.0 
    # Mantemos o heartbeat de Beta atual para garantir que ele está saudável
    beta.heartbeat()

    failed_detected = supervisor.check_health()
    print(f"Agentes declarados mortos pelo supervisor: {failed_detected}")
    assert "Agent-Alpha" in failed_detected, "O supervisor falhou em detectar a queda do Agent-Alpha!"
    assert beta.status == "HEALTHY", "O Agent-Beta foi indevidamente marcado como morto!"

    # --- Fase 3: Execução do Failover e Validação de Idempotência ---
    print("\n--- Fase 3: Execução do Failover ---")
    # Tentativa de re-executar a mesma ação (act_001) para testar idempotência no agente substituto (Agent-Beta)
    failover_result = supervisor.execute_failover(
        failed_agent_id="Agent-Alpha",
        task="Continuar processamento do lote A (retomada)",
        action_id="act_001", # ID repetido propositalmente para testar idempotência
        capability="data_processing"
    )
    print(failover_result)

    # Validações finais de sucesso
    assert "já executada anteriormente" in failover_result, "O sistema violou a idempotência e repetiu a ação externa!"
    print("\n[OK] Experimento concluído com sucesso e todas as asserções atendidas!")