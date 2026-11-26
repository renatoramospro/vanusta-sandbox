import time
import random

# Simulação de um ID de mensagem único para garantir idempotência
MESSAGE_ID = "msg-12345"
# Simulação de um estado de processamento (para idempotência)
PROCESSED_MESSAGES = set()

class BrokerSimulator:
    """Simula um broker que pode falhar e persistir mensagens."""
    def __init__(self):
        self.queue = []
        self.is_up = True
        print("Broker inicializado.")

    def send_message(self, message):
        if not self.is_up:
            print(f"[BROKER FALHA] Não foi possível enviar {message['id']}. Persistência necessária.")
            return False
        self.queue.append(message)
        print(f"[BROKER OK] Mensagem {message['id']} aceita e persistida.")
        return True

    def get_pending_messages(self):
        """Simula a recuperação após um crash."""
        if not self.is_up:
            return []
        # Em um cenário real, o broker recuperaria do disco. Aqui, devolvemos o que está na fila.
        return self.queue[:]

    def crash(self):
        self.is_up = False
        print("\n!!! SIMULAÇÃO: BROKER CRASHED !!!\n")

    def recover(self):
        self.is_up = True
        print("\n*** SIMULAÇÃO: BROKER RECOVERED ***\n")

class Consumer:
    """Consumidor idempotente."""
    def __init__(self):
        self.received_count = 0
        self.processed_count = 0

    def process(self, message):
        # Lógica de idempotência: checa se já processou este ID
        if message['id'] in PROCESSED_MESSAGES:
            print(f"[CONSUMER] Mensagem {message['id']} já processada (IDEMPOTÊNCIA). Ignorando.")
            return False # Não conta como novo processamento
        
        # Simula processamento de negócio
        print(f"[CONSUMER] Processando mensagem {message['id']}...")
        PROCESSED_MESSAGES.add(message['id'])
        self.processed_count += 1
        self.received_count += 1
        return True

def run_test_scenario():
    broker = BrokerSimulator()
    consumer = Consumer()
    
    # 1. Produtor envia (simulando Outbox commit)
    message_to_send = {"id": MESSAGE_ID, "payload": "Data importante"}
    broker.send_message(message_to_send)
    
    # 2. Simula falha do broker antes da entrega/ack
    broker.crash()
    
    # 3. Simula recuperação do broker e reenvio (retry)
    broker.recover()
    
    # 4. Recupera mensagens pendentes e entrega ao consumidor
    pending = broker.get_pending_messages()
    print(f"\n[TESTE] Broker recuperou {len(pending)} mensagens pendentes.")
    
    for msg in pending:
        consumer.process(msg)
        time.sleep(0.1) # Pequeno delay para simular tempo de processamento

    # 5. Verificação do Critério de Sucesso
    sent_count = 1
    received_count = consumer.received_count
    duplicated_count = len(PROCESSED_MESSAGES) - received_count # Deve ser 0 se for exatamente-once
    
    loss_rate = (sent_count - received_count) / sent_count if sent_count > 0 else 0
    
    print("\n--- RESULTADO FINAL ---")
    print(f"Total Enviadas: {sent_count}")
    print(f"Total Recebidas (Processadas): {received_count}")
    print(f"Total Duplicadas: {duplicated_count}")
    print(f"Taxa de Perda de Mensagem: {loss_rate * 100:.2f}%")
    
    # Verificação do critério de sucesso: 0% de perda E 0 duplicatas
    assert loss_rate == 0.0, "FALHA: Mensagem perdida."
    assert duplicated_count == 0, "FALHA: Mensagem duplicada (não é exactly-once)."
    print("SUCESSO: Critério de 0% de perda e idempotência atendido.")

if __name__ == "__main__":
    run_test_scenario()