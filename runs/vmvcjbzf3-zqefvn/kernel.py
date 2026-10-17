"""
Simulador de Microkernel Educacional em Python (Versão Corrigida).
Demonstra: Process Control Block (PCB), Troca de Contexto (Context Switching),
Espaço de Memória Isolado, Agendador (Scheduler) em Múltiplos Ticks e IPC Assíncrono.
"""

import sys
from collections import deque

# --- 1. Definição de Estados do Processo ---
STATE_READY = "READY"
STATE_RUNNING = "RUNNING"
STATE_BLOCKED = "BLOCKED"
STATE_TERMINATED = "TERMINATED"


# --- 2. Process Control Block (PCB) e Gerenciamento de Memória ---
class PCB:
    def __init__(self, pid: int, memory_limit: int, entry_point: int):
        self.pid = pid
        self.state = STATE_READY
        self.memory_limit = memory_limit  # Tamanho do espaço de memória isolado
        self.memory = [0] * memory_limit  # Espaço de memória privativo (simulado)
        self.registers = {
            "PC": entry_point,  # Program Counter (índice da instrução)
            "SP": memory_limit - 1,  # Stack Pointer
            "ACC": 0,  # Acumulador
        }
        self.ipc_queue = deque()  # Fila de mensagens recebidas (IPC)

    def write_memory(self, addr: int, value: int):
        """Escreve na memória privativa garantindo isolamento estrito."""
        if addr < 0 or addr >= self.memory_limit:
            raise MemoryError(
                f"[SEGFAULT] Processo {self.pid} tentou acessar endereço inválido {addr} (Limite: {self.memory_limit})"
            )
        self.memory[addr] = value

    def read_memory(self, addr: int) -> int:
        """Lê da memória privativa garantindo isolamento estrito."""
        if addr < 0 or addr >= self.memory_limit:
            raise MemoryError(
                f"[SEGFAULT] Processo {self.pid} tentou ler endereço inválido {addr} (Limite: {self.memory_limit})"
            )
        return self.memory[addr]

    def __repr__(self):
        return f"PCB(pid={self.pid}, state={self.state}, PC={self.registers['PC']}, ACC={self.registers['ACC']})"


# --- 3. Kernel do Microkernel ---
class Microkernel:

    def __init__(self):
        self.processes = {}
        self.ready_queue = deque()
        self.current_pid = None
        self.ipc_mailboxes = {}  # Mapeia PID -> Fila de mensagens do IPC

    def create_process(self, memory_limit: int, entry_point: int) -> int:
        pid = len(self.processes) + 1
        pcb = PCB(pid, memory_limit, entry_point)
        self.processes[pid] = pcb
        self.ipc_mailboxes[pid] = deque()
        self.ready_queue.append(pid)
        return pid

    def context_switch(self, next_pid: int):
        """Realiza a troca de contexto salvando e restaurando o estado."""
        if self.current_pid is not None:
            curr_pcb = self.processes[self.current_pid]
            if curr_pcb.state == STATE_RUNNING:
                curr_pcb.state = STATE_READY
                self.ready_queue.append(self.current_pid)

        self.current_pid = next_pid
        next_pcb = self.processes[next_pid]
        next_pcb.state = STATE_RUNNING
        # Remove da fila de prontos ao entrar em execução
        if next_pid in self.ready_queue:
            self.ready_queue.remove(next_pid)
        print(f"[KERNEL] Troca de contexto: CPU atribuída ao Processo {next_pid}")

    def run_scheduler_tick(self):
        """Simula um tick de clock do agendador (Round-Robin)."""
        if not self.ready_queue:
            print("[KERNEL] Agendador: Nenhum processo pronto na fila.")
            return

        next_pid = self.ready_queue.popleft()
        self.context_switch(next_pid)

    def ipc_send(self, dest_pid: int, message: str):
        """Envia uma mensagem para a caixa de correio IPC de outro processo."""
        if dest_pid not in self.processes:
            raise ValueError(f"[IPC] Erro: Processo destino {dest_pid} não existe.")
        self.ipc_mailboxes[dest_pid].append(message)
        print(f"[IPC] Mensagem enviada para PID {dest_pid}: '{message}'")

    def ipc_receive(self, pid: int) -> str:
        """Recebe uma mensagem da caixa de correio IPC do processo."""
        if pid not in self.ipc_mailboxes:
            raise ValueError(f"[IPC] Erro: Processo {pid} não possui caixa postal.")
        mailbox = self.ipc_mailboxes[pid]
        if not mailbox:
            return None
        msg = mailbox.popleft()
        print(f"[IPC] Processo {pid} recebeu mensagem: '{msg}'")
        return msg


# --- 4. Execução e Testes do Microkernel ---
def main():
    print("=== INICIALIZANDO MICROKERNEL EDUCACIONAL ===")
    kernel = Microkernel()

    # Criação de dois processos com isolamento de memória de 16 bytes
    pid1 = kernel.create_process(memory_limit=16, entry_point=0)
    pid2 = kernel.create_process(memory_limit=16, entry_point=0)

    print(f"Processo 1 criado com PID {pid1} (Memória: 16 bytes)")
    print(f"Processo 2 criado com PID {pid2} (Memória: 16 bytes)")

    # 1. Teste de Isolamento de Memória
    print("\n--- TESTE 1: Validação de Isolamento de Memória ---")
    p1 = kernel.processes[pid1]
    p2 = kernel.processes[pid2]

    p1.write_memory(0, 42)
    print(f"Processo {pid1} escreveu 42 no endereço 0.")
    print(f"Processo {pid1} lê endereço 0: {p1.read_memory(0)}")
    print(f"Processo {pid2} lê endereço 0 (deve ser 0): {p2.read_memory(0)}")
    assert (
        p2.read_memory(0) == 0
    ), "Falha no isolamento: Memória do Processo 2 foi corrompida!"

    # Tentativa de violação de memória (Segfault simulado)
    try:
        p1.write_memory(99, 100)
    except MemoryError as e:
        print(f"Capturado com sucesso: {e}")

    # 2. Teste de Troca de Contexto com Múltiplos Ticks (Scheduler Round-Robin)
    print("\n--- TESTE 2: Validação do Agendador em Múltiplos Ticks ---")
    kernel.run_scheduler_tick()  # Executa tick 1 (PID 1)
    assert kernel.current_pid == pid1, "O agendador deveria executar o PID 1"

    kernel.run_scheduler_tick()  # Executa tick 2 (PID 2)
    assert kernel.current_pid == pid2, "O agendador deveria alternar para o PID 2"

    kernel.run_scheduler_tick()  # Retorna para PID 1
    assert kernel.current_pid == pid1, "O agendador deveria retornar para o PID 1"

    # 3. Teste de IPC Assíncrono com Múltiplas Mensagens
    print("\n--- TESTE 3: Comunicação IPC Assíncrona ---")
    # Processo 1 envia duas mensagens para o Processo 2
    kernel.ipc_send(pid2, "Mensagem 1 do P1")
    kernel.ipc_send(pid2, "Mensagem 2 do P1")

    # Força execução do Processo 2 para ler as mensagens
    kernel.context_switch(pid2)

    msg1 = kernel.ipc_receive(pid2)
    msg2 = kernel.ipc_receive(pid2)

    assert msg1 == "Mensagem 1 do P1", "Primeira mensagem IPC corrompida ou perdida!"
    assert msg2 == "Mensagem 2 do P1", "Segunda mensagem IPC corrompida ou perdida!"

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO ===")


if __name__ == "__main__":
    main()