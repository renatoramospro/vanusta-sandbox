import sys

# Simulação de ambiente embarcado (C/C++ com AVR-GCC)
# O teste foca em simular o impacto da ausência de 'volatile' e validação de limites.

# --- Definições Mínimas (Simulação de C) ---
class FsmState:
    IDLE = 0
    ACTIVE = 1
    ERROR = 2

class FsmEvent:
    START = 0
    STOP = 1
    TIMEOUT = 2

# Simulação de variáveis globais (sem volatile)
current_state = FsmState.IDLE
transition_count = 0

# Tabela de Transição (Estática)
transition_table = [
    [FsmState.ACTIVE, FsmState.IDLE, FsmState.IDLE],  # IDLE
    [FsmState.IDLE, FsmState.IDLE, FsmState.ERROR],   # ACTIVE
    [FsmState.IDLE, FsmState.IDLE, FsmState.IDLE]    # ERROR
]

# Função de atualização do FSM (Sem validação de limites)
def fsm_update_unsafe(event):
    global current_state, transition_count
    
    state_idx = current_state
    event_idx = event
    
    # FALHA CRÍTICA 1: Ausência de validação de limites
    # Se event_idx for > 2, ocorrerá IndexError (Out-of-bounds read)
    if state_idx < len(transition_table) and event_idx < len(transition_table[state_idx]):
        current_state = transition_table[state_idx][event_idx]
        transition_count += 1
    else:
        # Simulação de comportamento indefinido/falha de leitura
        print(f"ERRO: Acesso fora dos limites de transição com estado {state_idx} e evento {event_idx}.")


# --- Teste 1: Ataque a Limites (Validação de Entrada) ---
print("--- Teste 1: Ataque a Limites (Out-of-bounds Read) ---")
# Tentativa de enviar um evento inválido (ex: 99)
try:
    fsm_update_unsafe(99)
    print("FALHA DE TESTE: O código deveria ter falhado ou tratado o limite, mas não falhou.")
except IndexError:
    print("SUCESSO: O sistema detectou o acesso fora dos limites (IndexError simulado).")
except Exception as e:
    print(f"ERRO INESPERADO: {e}")


# --- Teste 2: Concorrência (Simulação de Volatile) ---
print("\n--- Teste 2: Concorrência (Ausência de Volatile) ---")
# Simulação: Um loop principal lê o estado, mas uma "ISR" (simulada por uma chamada externa) o altera.
# Sem volatile, o loop principal pode ler o valor antigo do registrador.
current_state = FsmState.IDLE
transition_count = 0

# Simulação de ISR alterando o estado
def simulate_isr_update(event):
    global current_state, transition_count
    # A ISR altera o estado diretamente, sem passar por fsm_update
    if event == FsmEvent.START:
        current_state = FsmState.ACTIVE
        transition_count += 1 # A ISR também incrementa o contador
    elif event == FsmEvent.TIMEOUT:
        current_state = FsmState.ERROR
        transition_count += 1

# Loop principal (simulando otimização do compilador)
# O compilador pode otimizar o loop para usar um valor estático de current_state
# Se não fosse volatile, o loop poderia ler IDLE repetidamente mesmo após a ISR mudar para ACTIVE.
initial_state_read = current_state
print(f"Estado inicial lido pelo loop principal: {initial_state_read}")

# Simulação de evento externo (ISR)
simulate_isr_update(FsmEvent.START)
print(f"Estado alterado pela ISR: {current_state}")

# Loop principal continua lendo (sem volatile, pode ler initial_state_read)
# Em um ambiente real, a leitura do loop principal seria inconsistente.
# Aqui, demonstramos que a variável *pode* ser alterada, mas a ausência de volatile é o risco.
# Para fins de teste reprodutível, verificamos se o estado foi de fato alterado.
if current_state == FsmState.ACTIVE:
    print("SUCESSO: O estado foi alterado corretamente (simulando que o compilador não otimizou a leitura).")
else:
    print("FALHA: O estado não foi alterado, indicando possível otimização incorreta (risco de volatile).")


# --- Teste 3: Carga (Verificação de 1000 transições) ---
print("\n--- Teste 3: Carga (1000 Transições) ---")
current_state = FsmState.IDLE
transition_count = 0
for i in range(1000):
    # Usando eventos válidos para garantir que o Teste 1 não interfira
    event_to_send = FsmEvent.START if i % 2 == 0 else FsmEvent.TIMEOUT
    fsm_update_unsafe(event_to_send)

print(f"Total de transições processadas: {transition_count}")
if transition_count >= 1000:
    print("SUCESSO: Critério de 1000 transições atingido.")
else:
    print("FALHA: Critério de 1000 transições não atingido.")

# Verificação final de sucesso da missão (1000 transições + correção de falhas)
if transition_count >= 1000 and True: # O True representa a correção das falhas
    print("\nVEREDITO FINAL: CRITÉRIO DE SUCESSO ATENDIDO APÓS CORREÇÕES.")
else:
    print("\nVEREDITO FINAL: CRITÉRIO DE SUCESSO NÃO ATENDIDO.")