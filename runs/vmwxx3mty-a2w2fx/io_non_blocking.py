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
# Nota: set_inheritable é importante para processos filhos, mas mantemos para rigor
os.set_inheritable(r_fd, True)
os.set_inheritable(w_fd, True)
fcntl.fcntl(r_fd, fcntl.F_SETFL, flags)
fcntl.fcntl(w_fd, fcntl.F_SETFL, flags)

# --- Inicialização do Event Loop (epoll via select) ---
# select.epoll() é o wrapper Python para epoll
epoll_instance = select.epoll()
# CORREÇÃO CRÍTICA: Usar register() em vez de add()
# Adicionar AMBOS os FDs ao epoll, monitorando EPOLLIN (leitura)
epoll_instance.register(r_fd, select.EPOLLIN)
epoll_instance.register(w_fd, select.EPOLLIN) 

# --- Simulação de I/O ---
start_time = time.perf_counter()
requests_processed = 0
total_read_bytes = 0

# 1. Iniciar a escrita (simulando a requisição de I/O)
# Escreve 100 bytes, um para cada requisição
data_to_send = b'X' * NUM_REQUESTS
try:
    os.write(w_fd, data_to_send)
except OSError as e:
    # Tratamento de erro de escrita (embora improvável aqui)
    print(f"Erro ao escrever no pipe: {e}")
    exit(1)

# 2. Loop de Processamento Não Bloqueante
while requests_processed < NUM_REQUESTS:
    # Esperar eventos com um timeout pequeno (10ms)
    # CORREÇÃO CRÍTICA: Usar wait() ou poll() (wait é mais idiomático para epoll)
    events = epoll_instance.wait(timeout=0.01) 

    if not events:
        # Se não houver eventos, mas ainda faltam requisições, o loop deve parar
        break

    for fd, event in events:
        if event & select.EPOLLIN:
            # Tentativa de leitura não bloqueante
            try:
                # Lê 1 byte por vez para simular requisições discretas
                data = os.read(fd, 1) 
                if data:
                    requests_processed += 1
                    total_read_bytes += len(data)
                # Se data for vazio, o pipe foi fechado, mas o loop principal deve continuar se requests_processed < NUM_REQUESTS
            except OSError as e:
                # VERIFICAÇÃO DE NON-BLOCKING: Captura EAGAIN/EWOULDBLOCK
                if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    # I/O não estava pronto, comportamento não bloqueante confirmado.
                    pass 
                # ATACA EQUÍVOCO: Captura EBADF (Descritor Inválido) - Cenário Adversarial
                elif e.errno == errno.EBADF:
                    print("ERRO ADVERSARIAL CAPTURADO: EBADF. Limpando recurso.")
                    # Limpeza de recurso (unregister e close)
                    epoll_instance.unregister(fd)
                    os.close(fd)
                    # Não aborta a missão, apenas registra o incidente
                else:
                    # Outros erros críticos
                    print(f"Erro de I/O inesperado: {e}")
                    break
        
        # Nota: Não precisamos de lógica para EPOLLOUT neste pipe de simulação

# --- Finalização e Validação ---
end_time = time.perf_counter()
total_time_ms = (end_time - start_time) * 1000
success = total_read_bytes == NUM_REQUESTS and total_time_ms < TIMEOUT_MS

# Fechar FDs e limpar epoll
epoll_instance.unregister(r_fd)
epoll_instance.unregister(w_fd)
os.close(r_fd)
os.close(w_fd)

print(f"Requisições processadas: {requests_processed}/{NUM_REQUESTS}")
print(f"Tempo total de execução: {total_time_ms:.2f} ms")
print(f"Critério de sucesso (< {TIMEOUT_MS}ms): {success}")

# Garantir que o experimento termina com código 0 se o critério de latência for atendido
if not success:
    # Se falhar o critério de tempo, mas processar 100 requisições, ainda é um sucesso conceitual,
    # mas para o critério estrito, falha.
    assert False, "Falha no critério de latência ou processamento."
else:
    assert True, "Sucesso na latência e processamento."