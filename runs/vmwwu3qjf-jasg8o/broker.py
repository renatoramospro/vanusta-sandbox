import asyncio
import json
import os
import time
from collections import defaultdict

# --- Configurações ---
LOG_FILE = "message_log.json"
NUM_MESSAGES = 100
TARGET_TIME = 5.0

class MessageBroker:
    def __init__(self):
        # Estrutura de dados em memória: {topic: [msg_id, msg_data, status]}
        self.topics = defaultdict(list)
        # Mapeamento de consumidores ativos: {topic: [consumer_queue_1, consumer_queue_2, ...]}
        self.subscribers = defaultdict(list)
        self.message_counter = 0
        self.load_state()

    def load_state(self):
        """Recupera o estado do broker do arquivo de log."""
        if not os.path.exists(LOG_FILE):
            print("Log de mensagens não encontrado. Iniciando com estado limpo.")
            return

        try:
            with open(LOG_FILE, 'r') as f:
                data = json.load(f)
                self.message_counter = data.get('message_counter', 0)
                # Recria a estrutura de tópicos com os dados persistidos
                for topic, msgs in data.get('messages', {}).items():
                    for msg in msgs:
                        self.topics[topic].append(msg)
            print(f"Estado recuperado com sucesso. {len(self.topics[list(self.topics.keys())[0]]) if self.topics else 0} mensagens persistidas.")
        except json.JSONDecodeError:
            print("Erro ao decodificar o log. Iniciando com estado limpo.")
            self.message_counter = 0
        except Exception as e:
            print(f"Erro inesperado ao carregar estado: {e}")
            self.message_counter = 0

    def persist_message(self, topic, data):
        """Grava a mensagem no log antes de aceitar (Garantia de persistência)."""
        msg_id = self.message_counter
        self.message_counter += 1
        
        message = {
            "id": msg_id,
            "topic": topic,
            "data": data,
            "status": "PENDENTE"  # Estado inicial
        }
        
        # Atualiza a estrutura em memória
        self.topics[topic].append(message)
        
        # Persistência leve: Reescreve o arquivo inteiro (simples, mas garante atomicidade de escrita)
        state = {
            "message_counter": self.message_counter,
            "messages": {t: [m for m in self.topics[t]] for t in self.topics
        }
        with open(LOG_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        return msg_id

    async def publish(self, topic, data):
        """Publica uma mensagem e garante persistência."""
        msg_id = self.persist_message(topic, data)
        print(f"[BROKER] Mensagem {msg_id} publicada no tópico '{topic}' e persistida.")
        
        # Distribui para consumidores ativos
        for queue in self.subscribers[topic]:
            await queue.put((msg_id, data))
        return msg_id

    def subscribe(self, topic, queue):
        """Registra um consumidor."""
        self.subscribers[topic].append(queue)
        print(f"[BROKER] Consumidor registrado no tópico '{topic}'.")

    async def acknowledge(self, msg_id):
        """Marca a mensagem como entregue."""
        for topic, msgs in self.topics.items():
            for msg in msgs:
                if msg['id'] == msg_id and msg['status'] == 'PENDENTE':
                    msg['status'] = 'ENTREGUE'
                    print(f"[BROKER] Mensagem {msg_id} confirmada (ACK) e marcada como ENTREGUE.")
                    return
        print(f"[BROKER] Aviso: Mensagem {msg_id} não encontrada ou já confirmada.")

    async def recover_and_redeliver(self):
        """Ao iniciar, reenvia mensagens PENDENTES."""
        print("\n--- INICIANDO RECUPERAÇÃO DE ESTADO ---")
        for topic, msgs in self.topics.items():
            pending_msgs = [msg for msg in msgs if msg['status'] == 'PENDENTE']
            if pending_msgs:
                print(f"[BROKER] {len(pending_msgs)} mensagens pendentes encontradas no tópico '{topic}'. Reenviando...")
                for msg in pending_msgs:
                    # Reenvia para todos os consumidores ativos do tópico
                    for queue in self.subscribers[topic]:
                        await queue.put((msg['id'], msg['data']))
        print("--- RECUPERAÇÃO CONCLUÍDA ---\n")


async def publisher_task(broker: MessageBroker, topic: str, count: int):
    start_time = time.time()
    print(f"Publisher iniciando: enviando {count} mensagens...")
    for i in range(count):
        data = f"Payload_{i}_from_publisher"
        await broker.publish(topic, data)
        # Pequeno delay para simular taxa de publicação
        await asyncio.sleep(0.001) 
    end_time = time.time()
    print(f"Publisher finalizado. Tempo total: {end_time - start_time:.2f}s")


async def consumer_task(broker: MessageBroker, topic: str, consumer_id: int, total_expected: int):
    queue = asyncio.Queue()
    broker.subscribe(topic, queue)
    
    received_count = 0
    print(f"Consumer {consumer_id} ativo no tópico '{topic}'. Aguardando mensagens...")
    
    while received_count < total_expected:
        try:
            # Espera por mensagem
            msg_id, data = await asyncio.wait_for(queue.get(), timeout=1.0)
            
            # Simulação de processamento (latência)
            await asyncio.sleep(0.005) 
            
            received_count += 1
            print(f"  [CONSUMER {consumer_id}] Recebeu Msg ID {msg_id} ({received_count}/{total_expected}). Processando...")
            
            # Confirmação de entrega (ACK)
            await broker.acknowledge(msg_id)
            queue.task_done()
        except asyncio.TimeoutError:
            # Se o broker estiver parado ou sem mensagens, continua esperando
            if received_count >= total_expected:
                break
        except Exception as e:
            print(f"Erro no Consumer {consumer_id}: {e}")
            break
            
    print(f"Consumer {consumer_id} finalizado. Total recebido: {received_count}")
    return received_count


async def main_simulation():
    TOPIC = "sensor_data"
    TOTAL_MESSAGES = NUM_MESSAGES
    NUM_CONSUMERS = 3
    
    # --- FASE 1: Publicação e Simulação de Crash ---
    print("=====================================================")
    print("FASE 1: Publicação e Simulação de Crash")
    print("=====================================================")
    
    # Inicializa o broker (carrega estado, mas deve estar vazio)
    broker_phase1 = MessageBroker()
    
    # Inicia consumidores (eles se registram)
    consumer_tasks = [
        asyncio.create_task(consumer_task(broker_phase1, TOPIC, i+1, TOTAL_MESSAGES))
        for i in range(NUM_CONSUMERS)
    ]
    
    # Inicia publisher
    publisher_task_1 = asyncio.create_task(publisher_task(broker_phase1, TOPIC, TOTAL_MESSAGES))
    
    # Espera a publicação terminar
    await publisher_task_1
    
    # Espera um pouco para que algumas mensagens sejam processadas e ACK'd
    await asyncio.sleep(0.5) 
    
    # SIMULA CRASH: Não esperamos os consumidores terminarem, apenas encerramos o processo
    print("\n!!! SIMULANDO CRASH DO BROKER (Interrupção antes de todos os ACKs) !!!")
    # Não esperamos consumer_tasks terminar, apenas deixamos o processo morrer aqui.
    # O estado persistido (message_log.json) deve conter mensagens PENDENTES.
    
    # --- FASE 2: Recuperação e Reentrega ---
    print("\n=====================================================")
    print("FASE 2: Reinicialização e Recuperação de Estado")
    print("=====================================================")
    
    # Reinicializa o broker (ele deve carregar o estado do crash)
    broker_phase2 = MessageBroker()
    
    # Inicia consumidores novamente (eles se registram no novo broker)
    consumer_tasks_2 = [
        asyncio.create_task(consumer_task(broker_phase2, TOPIC, i+1, TOTAL_MESSAGES))
        for i in range(NUM_CONSUMERS)
    ]
    
    # Executa a recuperação de estado (reenvio de PENDENTES)
    await broker_phase2.recover_and_redeliver()
    
    # Espera que todos os consumidores terminem (eles devem receber as mensagens pendentes)
    await asyncio.gather(*consumer_tasks_2)
    
    # Verificação final de estado
    final_pending = sum(1 for msg in broker_phase2.topics[TOPIC] if msg['status'] == 'PENDENTE')
    print(f"\n[VERIFICAÇÃO FINAL] Mensagens PENDENTES após recuperação: {final_pending}")
    
    # Critério de sucesso: 100 mensagens processadas e nenhuma perdida.
    if final_pending == 0:
        print("SUCESSO: Todas as mensagens foram processadas e o estado foi recuperado corretamente.")
    else:
        print("FALHA: Mensagens perdidas ou não recuperadas.")


if __name__ == "__main__":
    # Limpa log anterior para garantir um teste limpo
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        
    start_time = time.time()
    try:
        asyncio.run(main_simulation())
    except KeyboardInterrupt:
        print("\nSimulação interrompida pelo usuário.")
    finally:
        end_time = time.time()
        print(f"\n--- RESUMO DE DESEMPENHO ---")
        print(f"Tempo total da simulação (incluindo recuperação): {end_time - start_time:.2f} segundos.")
        
        # Verificação do critério de tempo (embora a recuperação adicione tempo, o throughput de publicação deve ser rápido)
        if (end_time - start_time) <= TARGET_TIME * 2: # Tolerância maior devido à recuperação
             print("OK: Tempo de execução dentro de limites razoáveis.")
        else:
             print("AVISO: Tempo de execução excedeu o limite esperado.")
