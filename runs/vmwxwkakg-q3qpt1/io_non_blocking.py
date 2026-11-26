import os
import time
import epoll
import fcntl
import socket

# --- Configuração ---
NUM_REQUESTS = 100
TIMEOUT_MS = 50
# Usaremos um pipe para simular um I/O que eventualmente estará pronto
# Pipe: [read_fd, write_fd]
r_fd, w_fd = os.pipe()

# Configurar o FD de leitura como não bloqueante
flags = os.O_NONBLOCK
os.set_inheritable(r_fd, True)
os.set_inheritable(w_fd, True)
fcntl.fcntl(r_fd, fcntl.F_SETFL, flags)
fcntl.fcntl(w_fd, fcntl.F_SETFL, flags)

# --- Inicialização do Event Loop (epoll) ---
epoll_instance = epoll.epoll()
# Adicionar o FD de leitura ao epoll, monitorando eventos de leitura (EPOLLIN)
epoll_instance.add(r_fd, epoll.EPOLLIN)

# --- Simulação de I/O ---
start_time = time.perf_counter()
requests_processed = 0

# 1. Iniciar a escrita (simulando a requisição de I/O)
# Escreve um byte para sinalizar que dados estão disponíveis
os.write(w_fd, b'data')

# 2. Loop de Processamento Não Bloqueante
while requests_processed < NUM_REQUESTS:
    # Esperar eventos (timeout curto para garantir que o loop não trave se a simulação falhar)
    # O timeout aqui é para o epoll, não o tempo total da missão.
    events = epoll_instance.poll(timeout=0.01) 

    if not events:
        # Se não houver eventos, tentamos forçar o processamento se o I/O simulado já deveria ter ocorrido
        # Em um cenário real, esperaríamos o evento. Aqui, simulamos o processamento de requisições pendentes.
        pass
    
    for event in events:
        if event.data == r_fd:
            # Leitura não bloqueante
            try:
                data = os.read(r_fd, 1024)
                if data:
                    # Processar a requisição (simulação de processamento)
                    requests_processed += 1
                    # print(f"Processada requisição. Total: {requests_processed}")
                else:
                    # EOF
                    break
            except BlockingIOError:
                # Isso não deve ocorrer se o epoll disparou, mas é bom para robustez
                pass

# Fechar FDs
os.close(r_fd)
os.close(w_fd)

end_time = time.perf_counter()
total_time_ms = (end_time - start_time) * 1000

# --- Verificação do Critério de Sucesso ---
success = total_time_ms < TIMEOUT_MS

print(f"Total de requisições processadas: {requests_processed}")
print(f"Tempo total de execução: {total_time_ms:.2f} ms")
print(f"Critério de sucesso (< {TIMEOUT_MS}ms): {success}")

# Garantir que o experimento termina com código 0
assert success, "Falha no critério de latência."