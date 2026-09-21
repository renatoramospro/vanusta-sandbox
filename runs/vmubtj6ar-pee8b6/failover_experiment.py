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

    def execute_task(self, task: str, action_id: str, is_idempotent_action: bool = True) -> str:
        # Verifica idempotência: se a ação externa já foi registrada por este ou outro agente, não repete.
        if action_id in self.context_state.get("processed_actions", []):
            return f"[{self.agent_id}] Ação {action_id} já executada anteriormente. Ignorando repetição (Idempotência garantida)."
        
        # Execução normal
        self.context_state["history"].append({"task": task, "status": "executed"})
        if "processed_actions" not in self.context_state:
            self.context_state["processed_actions"] = []
        self.context_state["processed_actions"].append(action_id)
        self.action_log.append(action_id)
        return f"[{self.agent_id}] Tarefa executada com sucesso: {task} (Ação ID: {action_id})"

class VanustaSupervisor:
    """Supervisor responsável por monitorar, detectar falhas e executar o failover com contexto."""
    def __init__(self, heartbeat_timeout: float = 2.0):
        self.agents: Dict[str, AgentNode] = {}
        self.heartbeat_timeout = heartbeat_timeout
        self.task_registry: Dict[str, Dict[str, Any]] = {}

    ri_register_agent = lambda self, agent: self.agents.__setitem__(agent.agent_id, agent)

    def register_agent(self, agent: AgentNode):
        self.agents[agent.agent_id] = agent

    def monitor_and_detect_failures(self) -> List[str]:
        """Detecta agentes inativos com base no tempo de último heartbeat."""
        now = time.time()
        failed_agents = []
        for agent_id, agent in self.agents.items():
            if agent.status == "HEALTHY" and (now - agent.last_heartbeat) > self.heartbeat_timeout:
                agent.status = "DEAD"
                failed_agents.append(agent_id)
        return failed_agents

    def select_healthy_agent(self, required_capability: str, exclude_id: str) -> Optional[AgentNode]:
        """Seleciona um agente saudável baseado em capacidades (capability-based routing)."""
        for agent_id, agent in self.agents.items():
            if agent_id != exclude_id and agent.status == "HEALTHY" and required_capability in agent.capabilities:
                return agent
        return None

    def execute_failover(self, failed_agent_id: str, task: str, action_id: str, capability: str) -> str:
        """Executa o failover automático: detecta, migra estado cognitivo e retoma a tarefa."""
        print(f"\n[SUPORTE/ALERTA] Falha detectada no agente: {failed_agent_id}. Iniciando failover automático...")
        
        failed_agent = self.agents.get(failed_agent_id)
        cognitive_context = failed_agent.context_state if failed_agent else {"history": [], "processed_actions": []}

        # Seleciona substituto saudável
        substitute = self.select_healthy_agent(required_capability=capability, exclude_id=failed_agent_id)
        if not substitute:
            return "[FALHA] Nenhum agente saudável disponível com a capacidade exigida!"

        print(f"[FAILOVER] Transferindo contexto cognitivo de {failed_agent_id} para {substitute.agent_id}...")
        # Injeção de contexto cognitivo no novo agente
        substitute.context_state = cognitive_context

        # Retomada da tarefa com verificação de idempotência
        result = substitute.execute_task(task, action_id=action_id)
        return f"[SUCESSO] Failover concluído. Resposta do novo agente: {result}"

# ==========================================
# TESTE / DEMONSTRAÇÃO PRÉ-REQUISITA
# ==========================================
if __name__ == "__main__":
    print("=== INICIANDO EXPERIMENTO DE FAILOVER AUTOMÁTICO VANUSTA ===")
    
    supervisor = VanustaSupervisor(heartbeat_timeout=1.0)

    # 1. Criação de Agentes
    agent_alpha = AgentNode("Agent-Alpha", ["data_processing"])
    agent_beta = AgentNode("Agent-Beta", ["data_processing"])

    supervisor.register_agent(agent_alpha)
    supervisor.register_agent(agent_beta)

    # 2. Agente Alpha executa parte de uma tarefa e dispara uma ação externa (ex: API de pagamento/envio)
    print("\n--- Fase 1: Operação Normal ---")
    resp1 = agent_alpha.execute_task("Processar lote de dados A", action_id="act_001")
    print(resp1)

    # Simula falha do Agent-Alpha (interrompe heartbeats)
    print("\n--- Fase 2: Simulação de Queda do Agente Alpha ---")
    time.sleep(1.2) # Estoura o timeout de heartbeat (1.0s)
    failed_list = supervisor.monitor_and_detect_failures()
    print(f"Agentes declarados mortos pelo supervisor: {failed_list}")
    assert "Agent-Alpha" in failed_list, "O supervisor falhou em detectar a queda do Agent-Alpha!"

    # 3. Execução do Failover Automático com Transferência de Contexto e Idempotência
    print("\n--- Fase 3: Execução do Failover ---")
    # Tentativa de re-executar a mesma ação (act_001) para testar idempotência, mais a nova subtarefa
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