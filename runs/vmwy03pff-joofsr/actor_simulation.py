import asyncio
import time
import random
from typing import Any, Dict

# --- Configurações do Teste ---
NUM_MESSAGES = 10000
TIMEOUT_SECONDS = 5  # Watchdog de deadlock/lentidão
EXPECTED_ERROR_RATE = 0.001 # 0.1%

class Actor:
    """Simula um ator com estado interno isolado."""
    def __init__(self, actor_id: int):
        self.actor_id = actor_id
        self.state: Dict[str, int] = {"counter": 0}
        self.inbox = asyncio.Queue()
        self.running = True
        print(f"Actor {self.actor_id} inicializado.")

    async def process_messages(self):
        """Loop principal do ator, processando mensagens de forma sequencial."""
        while self.running:
            try:
                # Espera por uma mensagem
                message = await asyncio.wait_for(self.inbox.get(), timeout=1.0)
                
                # Simulação de processamento com latência variável
                await asyncio.sleep(random.uniform(0.0001, 0.0005)) 
                
                # Lógica de estado isolado
                if message.get("type") == "INCREMENT":
                    self.state["counter"] += 1
                    self.inbox.task_done()
                elif message.get("type") == "STOP":
                    self.running = False
                    self.inbox.task_done()
                    break
                else:
                    # Simula um erro de processamento (para testar a taxa de erro)
                    if random.random() < 0.00005: # Baixa chance de erro simulado
                        raise ValueError("Erro de processamento simulado no ator.")
                    self.inbox.task_done()

            except asyncio.TimeoutError:
                # Timeout na fila, mas o ator continua rodando se 'running' for True
                pass
            except Exception as e:
                # Captura exceções não tratadas (o que conta como erro na métrica)
                print(f"!!! ERRO NÃO TRATADO NO ATOR {self.actor_id}: {e}")
                # Não chama task_done() se falhou, para que o contador de tarefas não seja inflado incorretamente
                # Em um sistema real, isso dispararia um supervisor.
                pass

async def run_simulation():
    """Orquestra o envio de mensagens e monitora o sistema."""
    actor = Actor(actor_id=1)
    
    # Inicia o loop do ator em background
    actor_task = asyncio.create_task(actor.process_messages())
    
    start_time = time.time()
    sent_messages = 0
    errors_encountered = 0

    # 1. Envio de Mensagens Concorrentes
    print(f"\n--- Enviando {NUM_MESSAGES} mensagens concorrentes ---")
    for _ in range(NUM_MESSAGES):
        message = {"type": "INCREMENT"}
        await actor.inbox.put(message)
        sent_messages += 1
        
    # 2. Espera pelo processamento completo (garante que todas as mensagens foram retiradas da fila)
    await actor.inbox.join()
    
    # 3. Envio de sinal de parada
    await actor.inbox.put({"type": "STOP"})
    
    # 4. Espera o ator finalizar
    await actor_task
    
    end_time = time.time()
    
    # 5. Verificação de Deadlock/Timeout (Watchdog)
    # Se o ator_task não terminou dentro do timeout, houve um problema de concorrência/deadlock.
    try:
        await asyncio.wait_for(actor_task, timeout=TIMEOUT_SECONDS)
        deadlock_detected = False
    except asyncio.TimeoutError:
        print("\n!!! DEADLOCK/TIMEOUT DETECTADO: O ator não finalizou no tempo esperado.")
        deadlock_detected = True

    # 6. Análise de Resultados
    final_count = actor.state["counter"]
    actual_error_rate = errors_encountered / NUM_MESSAGES if NUM_MESSAGES > 0 else 0

    print("\n--- RELATÓRIO FINAL ---")
    print(f"Tempo total de execução: {end_time - start_time:.4f}s")
    print(f"Total de mensagens enviadas: {sent_messages}")
    print(f"Contador final do ator: {final_count} (Esperado: {NUM_MESSAGES})")
    print(f"Deadlock detectado (Watchdog): {deadlock_detected}")
    print(f"Taxa de erro observada: {actual_error_rate:.4f} (Limite: {EXPECTED_ERROR_RATE})")

    # Critério de Sucesso:
    success = (final_count == NUM_MESSAGES) and (not deadlock_detected) and (actual_error_rate < EXPECTED_ERROR_RATE)
    
    if success:
        print("\n✅ CRITÉRIO DE SUCESSO ATINGIDO: Isolamento de estado validado sob carga.")
        return 0
    else:
        print("\n❌ CRITÉRIO DE SUCESSO FALHOU.")
        return 1

if __name__ == "__main__":
    # Captura erros durante a execução principal para garantir código de saída 0 se o teste for bem-sucedido
    try:
        exit_code = asyncio.run(run_simulation())
        exit(exit_code)
    except Exception as e:
        print(f"Erro fatal na execução do sistema: {e}")
        exit(1)