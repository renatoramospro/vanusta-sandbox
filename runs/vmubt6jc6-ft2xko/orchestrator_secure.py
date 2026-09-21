import asyncio
import time
import random
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

# ==========================================
# 1. VALIDAÇÃO DE SCHEMA COM PYDANTIC (Segurança)
# ==========================================
class TaskPayload(BaseModel):
    id: int = Field(..., gt=0, description="ID único e positivo da tarefa")
    action: str = Field(..., min_length=3, max_length=50, description="Ação a ser executada")
    auth_token: str = Field(..., description="Token de autenticação para isolamento entre componentes")
    max_retries: int = Field(default=3, ge=0, le=5, description="Número máximo de tentativas")
    retry_count: int = Field(default=0, ge=0, description="Tentativas já realizadas")

# ==========================================
# 2. AGENTE VANUSTA COM AUTENTICAÇÃO E ISOLAMENTO
# ==========================================
class VanustaAgentSecure:
    def __init__(self, agent_id: int, secret_token: str):
        self.agent_id = agent_id
        self.secret_token = secret_token
        self.is_healthy = True

    async def execute_task(self, task: TaskPayload) -> str:
        # Validação de Autenticação (Isolamento entre componentes)
        if task.auth_token != self.secret_token:
            raise PermissionError(f"[Segurança] Agente {self.agent_id} rejeitou tarefa {task.id}: Token inválido ou não autorizado.")

        # Simula falha catastrófica se o agente estiver marcado como insaudável
        if not self.is_healthy:
            await asyncio.sleep(0.05)
            raise TimeoutError(f"Agente {self.agent_id} travou por timeout na tarefa {task.id}")
        
        # Simula tempo de processamento de I/O
        await asyncio.sleep(random.uniform(0.02, 0.05))
        return f"Sucesso: Tarefa {task.id} executada pelo Agente {self.agent_id}"

# ==========================================
# 3. ORQUESTRADOR COM BACKOFF EXPONENCIAL E DLQ
# ==========================================
class VanustaSecureOrchestrator:
    def __init__(self, shared_token: str):
        self.task_queue = asyncio.Queue()
        self.dead_letter_queue = []
        self.agents = {}
        self.next_agent_id = 1
        self.shared_token = shared_token
        self.metrics = {"processed": 0, "recovered": 0, "dead_lettered": 0, "latencies": []}
        self.running = False

    async def spawn_agent(self):
        agent_id = self.next_agent_id
        self.next_agent_id += 1
        agent = VanustaAgentSecure(agent_id, self.shared_token)
        self.agents[agent_id] = agent
        print(f"[Orquestrador] [+] Provisionando Agente Seguro {agent_id}")
        return agent_id

    async def supervisor_loop(self):
        """Monitora fila e gerencia recursos."""
        while self.running:
            if self.task_queue.qsize() > 2 and len(self.agents) < 3:
                await self.spawn_agent()
            await asyncio.sleep(0.05)

    async def submit_task(self, raw_data: Dict[str, Any]):
        """Valida e ingere tarefas com segurança."""
        try:
            # Validação estrita de schema impedindo injeção e payloads malformados
            validated_task = TaskPayload(**raw_data)
            await self.task_queue.put(validated_task)
        except ValidationError as e:
            print(f"[Segurança] Rejeitado: Payload inválido detectado -> {e.errors()}")
            self.metrics["dead_lettered"] += 1

    async def worker(self, worker_id: int):
        while self.running:
            try:
                task: TaskPayload = await asyncio.wait_for(self.task_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            agent = list(self.agents.values())[0] if self.agents else None
            if not agent:
                # Sem agentes, devolve para a fila
                await self.task_queue.put(task)
                self.task_queue.task_done()
                await asyncio.sleep(0.1)
                continue

            start_time = time.time()
            try:
                result = await agent.execute_task(task)
                latency = time.time() - start_time
                self.metrics["latencies"].append(latency)
                self.metrics["processed"] += 1
                print(f"[Executor] {result} (Latência: {latency:.3f}s)")
                self.task_queue.task_done()
            
            except (TimeoutError, PermissionError) as e:
                self.task_queue.task_done()
                task.retry_count += 1
                
                if task.retry_count <= task.max_retries:
                    # Implementação de Backoff Exponencial com Jitter (Anti-Retry Storm)
                    base_delay = 0.1
                    exponential_delay = base_delay * (2 ** (task.retry_count - 1))
                    jitter = random.uniform(0.01, 0.05)
                    total_backoff = exponential_delay + jitter
                    
                    self.metrics["recovered"] += 1
                    print(f"[Auto-Reparo] Falha tratada ({e}). Reencaminhando Tarefa {task.id} (Tentativa {task.retry_count}) com backoff de {total_backoff:.3f}s")
                    
                    # Simula espera do backoff antes de reintroduzir na fila
                    await asyncio.sleep(total_backoff)
                    await self.task_queue.put(task)
                else:
                    print(f"[Dead Letter Queue] Tarefa {task.id} excedeu o limite de tentativas. Movida para DLQ.")
                    self.dead_letter_queue.append(task)
                    self.metrics["dead_lettered"] += 1

    async def run(self, tasks_list):
        self.running = True
        await self.spawn_agent()
        
        supervisor_task = asyncio.create_task(self.supervisor_loop())
        workers = [asyncio.create_task(self.worker(i)) for i in range(2)]

        # Envia tarefas (incluindo uma maliciosa para testar validação de schema)
        for t in tasks_list:
            await self.submit_task(t)

        # Aguarda esvaziar a fila
        await self.task_queue.join()
        self.running = False

        supervisor_task.cancel()
        for w in workers:
            w.cancel()

# ==========================================
# 4. EXECUÇÃO DO EXPERIMENTO
# ==========================================
async def main():
    print("=== INICIANDO ORQUESTRADOR VANUSTA (VERSÃO SEGURA E RESILIENTE) ===")
    
    SECRET_KEY = "vanusta-secure-cluster-token-xyz"
    orchestrator = VanustaSecureOrchestrator(shared_token=SECRET_KEY)

    # Cenário de tarefas: inclui tarefas normais, uma com token inválido e uma com falha forçada
    tasks = [
        {"id": 1, "action": "analise_llm", "auth_token": SECRET_KEY},
        {"id": 2, "action": "geracao_codigo", "auth_token": SECRET_KEY},
        {"id": -99, "action": "invalida", "auth_token": SECRET_KEY}, # Deve falhar na validação Pydantic (Schema)
        {"id": 3, "action": "processamento_vetorial", "auth_token": "token_falsificado_malicioso"}, # Falha de autenticação
    ]

    await orchestrator.run(tasks)

    print("\n=== RELATÓRIO DE SEGURANÇA E MÉTRICAS ===")
    print(f"Tarefas processadas com sucesso: {orchestrator.metrics['processed']}")
    print(f"Falhas tratadas com Backoff Exponencial: {orchestrator.metrics['recovered']}")
    print(f"Tarefas rejeitadas/DLQ (Segurança/Validação): {orchestrator.metrics['dead_lettered']}")
    
    if orchestrator.metrics["latencies"]:
        avg_lat = sum(orchestrator.metrics["latencies"]) / len(orchestrator.metrics["latencies"])
        print(f"Tempo médio de resposta (Latência): {avg_lat:.3f}s")
    
    print("Status de Segurança: Isolamento autenticado e proteção contra Retry Storms ativos.")

    # Asserts de garantia de segurança e resiliência
    assert orchestrator.metrics["dead_lettered"] >= 2, "Erro: Validação de schema ou autenticação falhou em bloquear payloads indesejados!"
    print("\n[VEREDITO DO PROGRAMADOR]: Correções de segurança aplicadas, testadas e validadas com sucesso.")

if __name__ == "__main__":
    asyncio.run(main())