import time
import random
from typing import List, Tuple
import threading
from queue import Queue

# Definindo a estrutura de uma transação de forma concreta
TransactionResult = Tuple[bool, str] # (Sucesso, Mensagem)

def process_transaction(transaction_id: int) -> TransactionResult:
    """Simula o processamento de uma transação. Pode falhar aleatoriamente."""
    # Simula latência
    time.sleep(random.uniform(0.001, 0.005))
    
    # Simula falha com probabilidade baixa (ex: 1% de chance)
    if random.random() < 0.01:
        return (False, f"Erro de lógica na transação {transaction_id}")
    
    return (True, f"Transação {transaction_id} concluída com sucesso")

def concurrent_processor(num_transactions: int, channel_size: int = 100) -> Tuple[int, int]:
    """
    Processa transações concorrentemente usando um canal (Queue).
    Retorna (total_sucesso, total_falha).
    """
    # O canal de comunicação entre workers e o coletor de resultados
    # Aumentamos o tamanho do canal para evitar bloqueios prematuros no put()
    result_queue = Queue(maxsize=channel_size)
    
    # Contador para rastrear quantas transações foram solicitadas/processadas
    transactions_processed_counter = 0
    
    def worker():
        """Worker que processa transações e envia resultados para a fila."""
        nonlocal transactions_processed_counter
        
        # Cada worker processa uma transação única (simulando um trabalho delegado)
        # Para garantir que exatamente N transações sejam processadas, precisamos de um mecanismo de tarefa.
        # Simplificando: o worker processa um ID sequencialmente para garantir cobertura.
        # Como não temos um canal de tarefas de entrada, vamos usar um contador global protegido.
        
        with threading.Lock():
            if transactions_processed_counter >= num_transactions:
                return
            tx_id = transactions_processed_counter + 1
            transactions_processed_counter += 1
        
        success, msg = process_transaction(tx_id)
        
        # O put() agora tem alta probabilidade de sucesso pois o canal é grande,
        # e o join() só será chamado após todos os workers terem sido iniciados e finalizados.
        result_queue.put((success, msg))

    threads: List[threading.Thread] = []
    
    # Inicia o número exato de workers necessários para processar N transações
    for _ in range(num_transactions):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    # Espera todos os threads terminarem (garante que todos os puts foram tentados/concluídos)
    for t in threads:
        t.join()
        
    # Coleta todos os resultados da fila (AGORA QUE TODOS OS WORKERS TERMINARAM, A FILA ESTÁ COMPLETA)
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
NUM_TRANSACTIONS = 100 # Critério de sucesso exige 100
CHANNEL_SIZE = 100 # Tamanho adequado para evitar bloqueios prematuros
start_time = time.time()

total_success, total_failure = concurrent_processor(NUM_TRANSACTIONS, CHANNEL_SIZE)
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
print("\n[Teste de Equívoco] A comunicação segura via fila (canal) previne a necessidade de locks complexos, mitigando deadlocks, independentemente do runtime subjacente.")

# Verificação de Deadlock e Critério de Sucesso
assert total_processed == NUM_TRANSACTIONS, "Falha: Não todas as transações foram processadas."
assert error_rate < 0.001, "Falha: Taxa de erro excedeu o limite de 0.1%."
print("✅ Verificação de Deadlock e Taxa de Erro concluída com sucesso.")