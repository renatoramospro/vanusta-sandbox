"""
Simulador de Microkernel Educacional em Python.
Demonstra: Process Control Block (PCB), Troca de Contexto (Context Switching),
Espaço de Memória Isolado e Comunicação Inter-Processos (IPC) via Filas Seguras.
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
    def __init__(self, pid: int, memory_limit: int, entry_point):
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

    def create_process(self, memory_limit: int, entry_point) -> int:
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

        self.current_pid = next_pid
        next_pcb = self.processes[next_pid]
        next_pcb.state = STATE_RUNNING
        print(f"[KERNEL] Context Switch -> Processo {next_pid} ativado ({next_pcb})")

    def ipc_send(self, dest_pid: int, message: str):
        """Envia mensagem para a caixa de correio do processo de destino de forma controlada pelo kernel."""
        if dest_pid not in self.ipc_mailboxes:
            raise ValueError(f"[IPC] Processo de destino {dest_pid} não existe.")
        self.ipc_mailboxes[dest_pid].append(message)
        print(f"[KERNEL IPC] Mensagem enviada para PID {dest_pid}: '{message}'")

    def ipc_receive(self, pid: int) -> str:
        """Recebe mensagem da caixa de correio privativa. Se vazia, bloqueia o processo."""
        mailbox = self.ipc_mailboxes[pid]
        if not mailbox:
            # Bloqueia o processo se não houver mensagens (Simulando IPC síncrono/bloqueante)
            self.processes[pid].state = STATE_BLOCKED
            print(f"[KERNEL IPC] Processo {pid} bloqueado por falta de mensagens.")
            return None
        msg = mailbox.popleft()
        print(f"[KERNEL IPC] Processo {pid} recebeu mensagem: '{msg}'")
        return msg

    def run_scheduler_tick(self):
        """Executa um ciclo de escalonamento (Round-Robin simples)."""
        # Remove processos terminados ou bloqueados da fila ready
        active_ready = deque(
            [
                pid
                for pid in self.ready_queue
                if self.processes[pid].state == STATE_READY
            ]
        )

        if not active_ready:
            print("[KERNEL] Nenhum processo pronto para rodar.")
            return False

        next_pid = active_ready.popleft()
        active_ready.append(next_pid)
        self.ready_queue = active_ready

        if next_pid != self.current_pid:
            self.context_switch(next_pid)

        return True


# --- 4. Demonstração e Testes (Critério de Sucesso Robusto) ---
def main():
    print("=== INICIALIZANDO MICROKERNEL SIMPLIFICADO ===")
    kernel = Microkernel()

    # Criação de dois processos com espaços de memória isolados
    pid1 = kernel.create_process(memory_limit=16, entry_point=0)
    pid2 = kernel.create_process(memory_limit=16, entry_point=0)

    print(f"Processo 1 criado com PID {pid1} (Memória: 16 bytes)")
    print(f"Processo 2 criado com PID {pid2} (Memória: 16 bytes)")

    # 1. Teste de Isolamento de Memória (O equívoco comum: acesso direto à memória alheia)
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

    # 2. Teste de Troca de Contexto e IPC
    print("\n--- TESTE 2: Troca de Contexto e Comunicação IPC ---")
    kernel.run_scheduler_tick()  pid1 roda

    # Processo 1 envia mensagem para o Processo 2
    kernel.ipc_send(pid2, "Olá do Processo 1!")

    kernel.run_scheduler_tick()  # Alterna para pid2
    kernel.current_pid = pid2
    kernel.processes[pid2].state = STATE_RUNNING

    # Processo 2 lê a mensagem IPC
    msg = kernel.ipc_receive(pid2)
    assert msg == "Olá do Processo 1!", "Mensagem IPC corrompida ou perdida!"

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO ===")


if __name__ == "__main__":
    main()