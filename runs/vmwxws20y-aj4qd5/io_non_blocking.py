import os
import time
import select
import fcntl
import errno

# --- Configuração ---
NUM_REQUESTS = 100
TIMEOUT_MS = 50
# Usaremos um pipe para simular um I/O que eventualmente estará pronto
# Pipe: [read_fd, write_fd]
r_fd, w_fd = os.pipe()

# Configurar os FDs como não bloqueantes
flags = os.O_NONBLOCK
os.set_inheritable(r_fd, True)
os.set_inheritable(w_fd, True)
fcntl.fcntl(r_fd, fcntl.F_SETFL, flags)
fcntl.fcntl(w_fd, fcntl.F_SETFL, flags)

# --- Inicialização do Event Loop (epoll via select) ---
# select.epoll() é o wrapper Python para epoll
epoll_instance = select.epoll()
# Adicionar AMBOS os FDs ao epoll, monitorando EPOLLIN (leitura)
epoll_instance.add(r_fd, select.EPOLLIN)
# Embora não estejamos esperando escrita, monitorar ambos garante o controle total do FD
epoll_instance.add(w_fd, select.EPOLLIN) 

# --- Simulação de I/O ---
start_time = time.perf_counter()
requests_processed = 0

# 1. Iniciar a escrita (simulando a requisição de I/O)
# Escreve 100 bytes, um para cada requisição
data_to_send = b'X' * NUM_REQUESTS
os.write(w_fd, data_to_send)

# 2. Loop de Processamento Não Bloqueante
while requests_processed < NUM_REQUESTS:
    # Esperar eventos com um timeout pequeno (10ms)
    events = epoll_instance.poll(timeout=0.01) 

    if not events:
        # Se não houver eventos, mas ainda faltam requisições, algo está errado na simulação
        if requests_processed < NUM_REQUESTS:
            # Isso indica que o dado não chegou, o que não deve ocorrer com o write prévio
            break
        else:
            break

    for fd, event in events:
        if event & select.EPOLLIN:
            if fd == r_fd:
                # Tentar ler de forma não bloqueante
                try:
                    # Ler até que não haja mais dados disponíveis (loop de leitura)
                    while True:
                        data = os.read(r_fd, 1)
                        if not data:
                            # EOF
                            break
                        requests_processed += 1
                        # print(f"Processada requisição. Total: {requests_processed}")
                except OSError as e:
                    # Capturar EAGAIN/EWOULDBLOCK, indicando que não há mais dados AGORA
                    if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                        break
                    else:
                        # Outro erro fatal
                        raise

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