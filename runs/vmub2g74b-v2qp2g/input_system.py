from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional

class InputAction(Enum):
    JUMP = auto()
    ATTACK = auto()
    MOVE_LEFT = auto()

@dataclass(frozen=True)
class Command:
    action: InputAction
    timestamp: float

class InputMapper:
    """Responsável pelo remapeamento dinâmico de teclas para ações."""
    def __init__(self):
        self._mapping: Dict[str, InputAction] = {}

    def bind(self, raw_key: str, action: InputAction):
        self._mapping[raw_key] = action

    def get_action(self, raw_key: str) -> Optional[InputAction]:
        return self._mapping.get(raw_key)

class CommandBuffer:
    """Gerencia a janela de tempo de 150ms para os comandos."""
    def __init__(self, window_ms: float):
        self.window_sec = window_ms / 1000.0
        self.buffer: List[Command] = []

    def add(self, command: Command):
        self.buffer.append(command)

    def update(self, current_time: float):
        """Remove comandos que expiraram (TTL)."""
        self.buffer = [
            c for c in self.buffer 
            if (current_time - c.timestamp) <= self.window_sec
        ]

    def consume_next_valid(self, current_time: float) -> Optional[Command]:
        """
        Retorna o primeiro comando válido e o remove da fila.
        Não limpa o buffer inteiro, apenas o comando consumido.
        """
        self.update(current_time)
        if self.buffer:
            return self.buffer.pop(0)
        return None

class Player:
    """Simula o estado do personagem no jogo."""
    def __init__(self):
        self.is_grounded = True
        self.last_action = None

    def execute(self, command: Command):
        # Lógica de negócio: Só pode pular se estiver no chão
        if command.action == InputAction.JUMP and not self.is_grounded:
            return False
        
        self.last_action = command.action
        # Simula o efeito do comando
        if command.action == InputAction.JUMP:
            self.is_grounded = False
        return True

class InputSystem:
    """Orquestrador do sistema de input."""
    def __init__(self, mapper: InputMapper, buffer: CommandBuffer):
        self.mapper = mapper
        self.buffer = buffer

    def handle_raw_input(self, raw_key: str, current_time: float):
        action = self.mapper.get_action(raw_key)
        if action:
            self.buffer.add(Command(action, current_time))

# --- TESTES E DEMONSTRAÇÃO ---

def run_experiment():
    print("--- Iniciando Experimento de Arquitetura de Input ---")
    
    # Setup
    mapper = InputMapper()
    mapper.bind("SPACE", InputAction.JUMP)
    mapper.bind("Z", InputAction.ATTACK)
    
    buffer = CommandBuffer(window_ms=150)
    input_sys = InputSystem(mapper, buffer)
    player = Player()
    
    simulated_time = 0.0

    # TESTE 1: Buffering de Sucesso (Input no ar, execução no chão)
    print("\n[Teste 1] Buffering de precisão (Input no ar -> Execução no chão)...")
    simulated_time = 1.0
    input_sys.handle_raw_input("SPACE", simulated_time) # Pressionou JUMP
    player.is_grounded = False # Personagem está no ar, comando falharia se fosse imediato
    
    # Avança 100ms (dentro da janela de 150ms)
    simulated_time += 0.100 
    player.is_grounded = True # Personagem tocou o chão
    
    cmd = buffer.consume_next_valid(simulated_time)
    if cmd and player.execute(cmd):
        print(f"  ✅ Sucesso: Comando {cmd.action} executado após {simulated_time-1.0:.3f}s")
    else:
        print("  ❌ Falha: Comando não foi recuperado do buffer")

    # TESTE 2: Expiração (Input muito antigo)
    print("\n[Teste 2] Expiração de comando (Input fora da janela de 150ms)...")
    simulated_time = 2.0
    input_sys.handle_raw_input("SPACE", simulated_time)
    
    # Avança 200ms (fora da janela de 150ms)
    simulated_time += 0.200
    cmd = buffer.consume_next_valid(simulated_time)
    if cmd is None:
        print(f"  ✅ Sucesso: Comando expirou corretamente após {simulated_time-2.0:.3f}s")
    else:
        print(f"  ❌ Falha: Comando {cmd.action} ainda estava no buffer!")

    # TESTE 3: Troca de Dispositivo sem perda de estado
    print("\n[Teste 3] Troca de dispositivo (Remapeamento dinâmico)...")
    simulated_time = 3.0
    # Atualmente SPACE é JUMP. Vamos mudar para 'BUTTON_A' (Gamepad)
    mapper.bind("BUTTON_A", InputAction.JUMP)
    
    input_sys.handle_raw_input("BUTTON_A", simulated_time)
    cmd = buffer.consume_next_valid(simulated_time)
    if cmd and cmd.action == InputAction.JUMP:
        print("  ✅ Sucesso: Novo dispositivo mapeado e funcionando.")
    else:
        print("  ❌ Falha: Remapeamento não funcionou.")

    # TESTE 4: Ataque ao Equívoco Comum (Limpeza agressiva do buffer)
    print("\n[Teste 4] Contra-exemplo: Evitando limpeza agressiva do buffer...")
    simulated_time = 4.0
    input_sys.handle_raw_input("SPACE", simulated_time) # JUMP
    input_sys.handle_raw_input("Z", simulated_time)     # ATTACK (quase simultâneo)
    
    # Processa o primeiro (JUMP)
    cmd1 = buffer.consume_next_valid(simulated_time)
    # Se o sistema limpar o buffer todo aqui, o ATTACK some.
    # Vamos verificar se o ATTACK ainda está lá.
    cmd2 = buffer.consume_next_valid(simulated_time)
    
    if cmd1 and cmd1.action == InputAction.JUMP and cmd2 and cmd2.action == InputAction.ATTACK:
        print("  ✅ Sucesso: Múltiplos comandos preservados no buffer.")
    else:
        print("  ❌ Falha: O segundo comando foi perdido (Limpeza agressiva detectada)!")

if __name__ == "__main__":
    run_experiment()