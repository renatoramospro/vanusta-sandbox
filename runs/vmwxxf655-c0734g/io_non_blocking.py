import os
import time
import select
import fcntl
import errno

# --- Configuração ---
NUM_REQUESTS = 100
TIMEOUT_MS = 50
# Pipe: [read_fd, write_fd]
r_fd, w_fd = os.pipe()

# Configurar os FDs como não bloqueantes
flags = os.O_NONBLOCK
os.set_inheritable(r_fd, True)
os.set_inheritable(w_fd, True)
fcntl.fcntl(r_fd, fcntl.F_SETFL, flags)
fcntl.fcntl(w_fd, fcntl.F_SETFL, flags)

# --- Inicialização do Event Loop (epoll via select) ---
epoll_instance = select.epoll()
# Registrar AMBOS os FDs, monitorando EPOLLIN e eventos de controle
epoll_instance.register(r_fd, select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR)
epoll_instance.register(w_fd, select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR) 

# --- Simulação de I/O ---
start_time = time.perf_counter()
requests_processed = 0
total_read_bytes = 0
pipe_closed = False

# 1. Iniciar a escrita (simulando a requisição de I/O)
data_to_send = b'X' * NUM_REQUESTS
try:
    os.write(w_fd, data_to_send)
except OSError as e:
    print(f"Erro ao escrever no pipe: {e}")
    exit(1)

# 2. Loop de Processamento Não Bloqueante
while requests_processed < NUM_REQUESTS and not pipe_closed:
    # CORREÇÃO CRÍTICA: Usar poll() em vez de wait()
    # Timeout de 10ms para garantir que o tempo total < 50ms seja testável
    events = epoll_instance.poll(timeout=0.01) 

    if not events:
        # Timeout sem eventos, mas ainda esperamos requisições
        continue

    for fd, event in events:
        # Tratamento de eventos de controle (HUP/ERR)
        if event & (select.EPOLLHUP | select.EPOLLERR):
            print(f"Evento de controle detectado no FD {fd}. Fechando canal.")
            pipe_closed = True
            epoll_instance.unregister(fd)
            os.close(fd)
            continue
        
        # Tratamento de evento de leitura
        if event & select.EPOLLIN:
            try:
                # Lê 1 byte por vez para simular requisições discretas
                data = os.read(fd, 1) 
                if data:
                    requests_processed += 1
                    total_read_bytes += len(data)
                else:
                    # Pipe fechado pelo outro lado (EOF)
                    pipe_closed = True
                    epoll_instance.unregister(fd)
                    os.close(fd)
            except OSError as e:
                # VERIFICAÇÃO DE NON-BLOCKING: Captura EAGAIN/EWOULDBLOCK
                if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    pass # Comportamento não bloqueante confirmado
                # ATACA EQUÍVOCO: Captura EBADF (Descritor Inválido) - Cenário Adversarial
                elif e.errno == errno.EBADF:
                    print("ERRO ADVERSARIAL CAPTURADO: EBADF. Limpando recurso.")
                    epoll_instance.unregister(fd)
                    os.close(fd)
                    pipe_closed = True
                    break
    
    # Se o loop de eventos detectou fechamento, saímos do loop principal
    if pipe_closed and requests_processed < NUM_REQUESTS:
        break

# Finalização e Validação
end_time = time.perf_counter()
total_time_ms = (end_time - start_time) * 1000

print(f"--- Relatório de Execução ---")
print(f"Requisições Processadas: {requests_processed}/{NUM_REQUESTS}")
print(f"Tempo Total de Execução: {total_time_ms:.2f} ms")

# Critério de Sucesso: 100 requisições com latência total < 50ms
assert requests_processed == NUM_REQUESTS, "Falha: Não processou todas as 100 requisições."
assert total_time_ms < TIMEOUT_MS, f"Falha: Latência ({total_time_ms:.2f}ms) excedeu o limite de {TIMEOUT_MS}ms."

print("SUCESSO: Critério de latência e processamento atendido.")