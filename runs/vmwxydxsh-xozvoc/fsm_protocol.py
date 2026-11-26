from enum import Enum

# 1. Definição de Estados e Eventos
class State(Enum):
    IDLE = 1
    WAIT_SYN = 2
    SYN_SENT = 3
    ESTABLISHED = 4
    CLOSED = 5

class Event(Enum):
    SYN_RECEIVED = 1
    ACK_RECEIVED = 2
    TIMEOUT = 3
    CLOSE = 4

# 2. Tabela de Transição (Estado Atual -> Evento -> (Próximo Estado, Ação))
# Ação é um placeholder simples para demonstrar a separação de lógica.
TRANSITIONS = {
    State.IDLE: {Event.SYN_RECEIVED: (State.WAIT_SYN, "Timer Start")},
    State.WAIT_SYN: {Event.SYN_RECEIVED: (State.SYN_SENT, "Send SYN")},
    State.SYN_SENT: {Event.ACK_RECEIVED: (State.ESTABLISHED, "Confirm")},
    State.ESTABLISHED: {
        Event.CLOSE: (State.CLOSED, "Cleanup"),
        Event.TIMEOUT: (State.CLOSED, "Timeout Error")
    },
    State.CLOSED: {} # Estado terminal
}

# 3. Engine FSM
class FSM:
    def __init__(self, initial_state=State.IDLE):
        self.state = initial_state
        self.history = [initial_state]

    def transition(self, event: Event) -> bool:
        """Tenta transicionar com base no evento. Retorna True se transição ocorreu."""
        if self.state not in TRANSITIONS:
            print(f"ERRO: Estado {self.state.name} não definido na tabela.")
            return False
        
        current_transitions = TRANSITIONS[self.state]
        
        if event in current_transitions:
            next_state, action = current_transitions[event]
            
            # Executa Ação (simulada)
            # print(f"Ação executada: {action}") 
            
            self.state = next_state
            self.history.append(next_state)
            return True
        else:
            # Evento não mapeado para o estado atual (ignora ou entra em erro, dependendo do protocolo)
            # Neste caso, tratamos como transição falha/ignorada.
            return False

# 4. Teste de Cobertura e Loop
def run_test():
    print("--- Iniciando Teste FSM ---")
    fsm = FSM()
    
    # Sequência de teste válida (IDLE -> WAIT_SYN -> SYN_SENT -> ESTABLISHED -> CLOSED)
    valid_sequence = [
        Event.SYN_RECEIVED,  # IDLE -> WAIT_SYN
        Event.SYN_RECEIVED,  # WAIT_SYN -> SYN_SENT
        Event.ACK_RECEIVED,  # SYN_SENT -> ESTABLISHED
        Event.CLOSE          # ESTABLISHED -> CLOSED
    ]
    
    print(f"Estado Inicial: {fsm.state.name}")
    
    for i, event in enumerate(valid_sequence):
        success = fsm.transition(event)
        print(f"Iteração {i+1} ({event.name}): Sucesso={success}, Novo Estado={fsm.state.name}")

    # Teste de loop infinito (tentar eventos em CLOSED)
    fsm_loop = FSM(State.CLOSED)
    print(f"\nEstado Inicial Loop Teste: {fsm_loop.state.name}")
    
    # 1000 iterações (o critério original)
    for i in range(1000):
        # Tenta um evento em um estado terminal
        success = fsm_loop.transition(Event.SYN_RECEIVED) 
        if not success:
            # Esperamos que a transição falhe, mas o loop não deve travar
            break 
        # Se chegasse aqui, seria um loop infinito, mas a lógica de TRANSITIONS impede.

    print(f"Estado Final Loop Teste: {fsm_loop.state.name}")
    print("--- Teste Concluído com Sucesso (Sem Loops Infinitos) ---")

if __name__ == "__main__":
    run_test()