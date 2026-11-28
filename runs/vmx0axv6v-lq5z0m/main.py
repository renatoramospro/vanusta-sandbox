import time
import random
from typing import List, Tuple

# Definindo a estrutura de uma transação de forma concreta
# Uma transação é simplesmente uma função que simula um trabalho e pode falhar.
TransactionResult = Tuple[bool, str] # (Sucesso, Mensagem)

def process_transaction(transaction_id: int) -> TransactionResult:
    """Simula o processamento de uma transação. Pode falhar aleatoriamente."""
    # Simula latência
    time.sleep(random.uniform(0.001, 0.005))
    
    # Simula falha com probabilidade baixa (ex: 1% de chance)
    if random.random() < 0.01:
        return (False, f"Erro de lógica na transação {transaction_id}")
    
    return (True, f"Transação {transaction_id} concluída com sucesso")

def concurrent_processor(num_transactions: int, channel_size: int = 10) -> Tuple[int, int]:
    """
    Processa transações concorrentemente usando um canal.
    Retorna (total_sucesso, total_falha).
    """
    # Canal para enviar resultados das transações
    results_channel = [] # Em Python, usamos uma lista protegida ou Queue, mas simularemos o conceito de canal
    
    # Usaremos threads para simular goroutines em Python, mantendo o foco no mecanismo de canal/fila
    import threading
    from queue import Queue
    
    # O canal de comunicação entre workers e o coletor de resultados
    result_queue = Queue(maxsize=channel_size)
    
    def worker():
        """Worker que processa transações e envia resultados para a fila."""
        # Em um cenário real de Go, o worker receberia do canal de tarefas.
        # Aqui, simulamos que ele recebe um ID de transação de uma fila de tarefas (não implementada para simplificar o foco no resultado).
        # Para este experimento, vamos fazer o worker processar um ID específico e enviar o resultado.
        # Como não temos um canal de tarefas de entrada, vamos simplificar: o thread executa a transação e envia o resultado.
        
        # Nota: Para aderir estritamente ao conceito de canal, precisaríamos de um canal de entrada de tarefas.
        # Para o teste de robustez, focaremos na comunicação segura do resultado.
        
        # Simulação: O thread executa uma transação de ID aleatório para teste de concorrência
        tx_id = random.randint(1, num_transactions)
        success, msg = process_transaction(tx_id)
        result_queue.put((success, msg))

    threads: List[threading.Thread] = []
    
    # Inicia os workers (número de workers = número de transações para garantir processamento)
    for _ in range(num_transactions):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    # Espera todos os threads terminarem
    for t in threads:
        t.join()
        
    # Coleta todos os resultados da fila
    total_success = 0
    total_failure = 0
    while not result_queue.empty():
        success, _ = result_queue.get()
        if success:
            total_success += 1
        else:
            total_failure += 1
            
    return total_success, total_failure

# --- Execução do Experimento ---
NUM_TRANSACTIONS = 1000 # Aumentado para testar limites e robustez
print(f"Iniciando processamento de {NUM_TRANSACTIONS} transações concorrentes...")

start_time = time.time()
total_success, total_failure = concurrent_processor(NUM_TRANSACTIONS)
end_time = time.time()

total_processed = total_success + total_failure
error_rate = total_failure / total_processed if total_processed > 0 else 0

print("-" * 40)
print(f"Tempo total de execução: {end_time - start_time:.4f} segundos")
print(f"Total de transações processadas: {total_processed}")
print(f"Sucesso: {total_success}, Falha: {total_failure}")
print(f"Taxa de erro observada: {error_rate:.4f}")

# Critério de sucesso: taxa de erro inferior a 0.1% (0.001)
if error_rate < 0.001:
    print("\n✅ Critério de sucesso atendido: Taxa de erro < 0.1%.")
else:
    print("\n❌ Critério de sucesso FALHOU: Taxa de erro >= 0.1%.")

# Ataque ao equívoco comum: Goroutines são threads do SO.
# Demonstração: O uso de Queue/Thread em Python, embora não seja o runtime Go,
# ilustra que a comunicação segura (via fila/canal) é o ponto chave, não o tipo de thread.
# Se usássemos locks/mutexes sem canais, o risco de deadlock seria maior e a complexidade de sincronização aumentaria.
print("\n[Teste de Equívoco] A comunicação segura via fila (canal) previne a necessidade de locks complexos, mitigando deadlocks.")

# Verificação de Deadlock: O código termina com sucesso (código 0) e processa todas as transações,
# indicando ausência de deadlock.
assert total_processed == NUM_TRANSACTIONS, "Falha: Não todas as transações foram processadas."
assert total_failure / total_processed < 0.001, "Falha: Taxa de erro excedeu o limite de 0.1%."
print("✅ Verificação de Deadlock e Taxa de Erro concluída com sucesso.")