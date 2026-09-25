import pytest

# Definição dos Opcodes
OP_PUSH  = 1  # Empurra um literal para a pilha
OP_POP   = 2  # Remove o elemento do topo da pilha
OP_ADD   = 3  # Adiciona os dois elementos do topo
OP_SUB   = 4  # Subtrai o topo do penúltimo
OP_MUL   = 5  # Multiplica os dois elementos do topo
OP_DIV   = 6  # Divide o penúltimo pelo topo
OP_LOAD  = 7  # Carrega uma variável local para a pilha
OP_STORE = 8  # Retira o topo e armazena na variável local
OP_JMP   = 9  # Salto incondicional
OP_JMPF  = 10 # Salto condicional se falso (retira o topo)
OP_EQ    = 11 # Testa igualdade (a == b)
OP_LT    = 12 # Testa menor que (a < b)
OP_HALT  = 99 # Para a execução

class StackVM:
    def __init__(self, code, debug=False):
        self.code = code
        self.pc = 0
        self.stack = []
        self.locals = {}
        self.debug = debug

    def run(self):
        while self.pc < len(self.code):
            instruction = self.code[self.pc]
            op = instruction[0]
            
            if self.debug:
                print(f"PC: {self.pc} | Op: {op} | Stack: {self.stack} | Locals: {self.locals}")

            if op == OP_PUSH:
                self.stack.append(instruction[1])
                self.pc += 1
            elif op == OP_POP:
                self.stack.pop()
                self.pc += 1
            elif op == OP_ADD:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
                self.pc += 1
            elif op == OP_SUB:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)
                self.pc += 1
            elif op == OP_MUL:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
                self.pc += 1
            elif op == OP_DIV:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a // b)
                self.pc += 1
            elif op == OP_LOAD:
                var_name = instruction[1]
                val = self.locals.get(var_name, 0)
                self.stack.append(val)
                self.pc += 1
            elif op == OP_STORE:
                var_name = instruction[1]
                val = self.stack.pop()
                self.locals[var_name] = val
                self.pc += 1
            elif op == OP_JMP:
                self.pc = instruction[1]
            elif op == OP_JMPF:
                condition = self.stack.pop()
                if not condition:
                    self.pc = instruction[1]
                else:
                    self.pc += 1
            elif op == OP_EQ:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a == b else 0)
                self.pc += 1
            elif op == OP_LT:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a < b else 0)
                self.pc += 1
            elif op == OP_HALT:
                break
            else:
                raise ValueError(f"Opcode desconhecido: {op} no PC={self.pc}")

# --- Testes Automatizados com Pytest ---

def test_factorial_5():
    """
    Programa em bytecode para calcular o fatorial de 5 (5! = 120).
    Lógica em pseudocódigo:
    n = 5
    acc = 1
    while n > 1:
        acc = acc * n
        n = n - 1
    """
    code = [
        (OP_PUSH, 5),   # 0: n = 5
        (OP_STORE, 'n'),
        (OP_PUSH, 1),   # 2: acc = 1
        (OP_STORE, 'acc'),
        # LOOP_START (PC: 4)
        (OP_LOAD, 'n'), # 4: carrega n
        (OP_PUSH, 1),   # 5: carrega 1
        (OP_LT,     ),  # 6: n < 1 (na verdade queremos testar n > 1, ou n == 1 para sair)
        # Vamos fazer diferente para simplificar os saltos:
        # Loop enquanto n > 0: decrementa n e multiplica acc
    ]
    
    # Redefinindo o bytecode do fatorial de forma limpa e robusta:
    # n = 5, acc = 1
    # [0] PUSH 5
    # [1] STORE 'n'
    # [2] PUSH 1
    # [3] STORE 'acc'
    # -- LOOP (PC 4) --
    # [4] LOAD 'n'
    # [5] PUSH 0
    # [6] EQ
    # [7] JMPF 14 (se n == 0 for falso, continua o loop)
    # [8] JMP 18 (se n == 0 for verdadeiro, sai do loop) -> Simplificado abaixo
    
    # Fatorial direto e elegante:
    fact_code = [
        (OP_PUSH, 5),
        (OP_STORE, 'n'),
        (OP_PUSH, 1),
        (OP_STORE, 'result'),
        # 4: Loop check
        (OP_LOAD, 'n'),
        (OP_PUSH, 1),
        (OP_LT),         # se n < 1, sai do loop
        (OP_JMPF, 15),   # se falso (n >= 1), continua para o corpo do loop
        (OP_JMP, 20),    # sai do loop (pulando para o fim)
        # 9: Corpo do loop (PC 9)
        (OP_LOAD, 'result'),
        (OP_LOAD, 'n'),
        (OP_MUL),
        (OP_STORE, 'result'),
        (OP_LOAD, 'n'),
        (OP_PUSH, 1),
        (OP_SUB),
        (OP_STORE, 'n'),
        (OP_JMP, 4),     # volta para o início do loop
        # 19: Fim
        (OP_LOAD, 'result'),
        (OP_HALT)
    ]
    
    # Ajuste preciso dos índices de salto para o fact_code acima:
    # 0: PUSH 5
    # 1: STORE 'n'
    # 2: PUSH 1
    # 3: STORE 'result'
    # --- INÍCIO DO LOOP (PC: 4) ---
    # 4: LOAD 'n'
    # 5: PUSH 0
    # 6: EQ           (n == 0?)
    # 7: JMPF 10      (se n != 0, pula para o corpo do loop em PC 10)
    # 8: JMP 17       (se n == 0, sai para PC 17)
    # --- CORPO DO LOOP (PC: 10) ---
    # 10: LOAD 'result'
    # 11: LOAD 'n'
    # 12: MUL
    # 13: STORE 'result'
    # 14: LOAD 'n'
    # 15: PUSH 1
    # 16: SUB
    # 17: STORE 'n'
    # 18: JMP 4       (retorna para o início do loop)
    # --- FIM (PC: 19) ---
    # 19: LOAD 'result'
    # 20: HALT
    
    corrected_fact_code = [
        (OP_PUSH, 5),       # 0
        (OP_STORE, 'n'),    # 1
        (OP_PUSH, 1),       # 2
        (OP_STORE, 'result'),# 3
        # Loop start (4)
        (OP_LOAD, 'n'),     # 4
        (OP_PUSH, 0),       # 5
        (OP_EQ),            # 6
        (OP_JMPF, 10),      # 7 -> se n != 0, vai para o corpo (10)
        (OP_JMP, 19),       # 8 -> se n == 0, vai para o fim (19)
        (OP_NOP_PLACEHOLDER,), # 9 (opcional, mantido para alinhamento se necessário, ou ajustado)
        # Corpo (10)
        (OP_LOAD, 'result'),# 10
        (OP_LOAD, 'n'),     # 11
        (OP_MUL),           # 12
        (OP_STORE, 'result'),# 13
        (OP_LOAD, 'n'),     # 14
        (OP_PUSH, 1),       # 15
        (OP_SUB),           # 16
        (OP_STORE, 'n'),    # 17
        (OP_JMP, 4),        # 18 -> volta ao topo do loop
        # Fim (19)
        (OP_LOAD, 'result'),# 19
        (OP_HALT)           # 20
    ]

    vm = StackVM(corrected_fact_code, debug=False)
    vm.run()
    
    # O topo da pilha deve conter o resultado de 5! = 120
    assert vm.stack.pop() == 120

def test_counter_example_wrong_stack_ops():
    """
    Contraexemplo pedagógico: Ordem dos operandos na pilha (LIFO).
    Operações não comutativas como subtração exigem que o topo seja o subtraendo
    e o penúltimo seja o minuendo.
    """
    code_correct = [
        (OP_PUSH, 5),
        (OP_PUSH, 3),
        (OP_SUB,),
        (OP_HALT,)
    ]
    vm = StackVM(code_correct)
    vm.run()
    assert vm.stack.pop() == 2 # 5 - 3 = 2