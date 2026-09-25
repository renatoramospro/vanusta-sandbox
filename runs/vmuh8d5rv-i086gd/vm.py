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
        code_len = len(self.code)
        while self.pc < code_len:
            instr = self.code[self.pc]
            opcode = instr[0]
            arg = instr[1] if len(instr) > 1 else None

            if self.debug:
                print(f"PC: {self.pc} | Op: {opcode} | Arg: {arg} | Stack: {self.stack} | Locals: {self.locals}")

            if opcode == OP_PUSH:
                self.stack.append(arg)
                self.pc += 1
            elif opcode == OP_POP:
                self.stack.pop()
                self.pc += 1
            elif opcode == OP_ADD:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
                self.pc += 1
            elif opcode == OP_SUB:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)
                self.pc += 1
            elif opcode == OP_MUL:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
                self.pc += 1
            elif opcode == OP_DIV:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a // b) # Divisão inteira
                self.pc += 1
            elif opcode == OP_LOAD:
                val = self.locals.get(arg, 0)
                self.stack.append(val)
                self.pc += 1
            elif opcode == OP_STORE:
                val = self.stack.pop()
                self.locals[arg] = val
                self.pc += 1
            elif opcode == OP_JMP:
                self.pc = arg
            elif opcode == OP_JMPF:
                cond = self.stack.pop()
                if not cond:
                    self.pc = arg
                else:
                    self.pc += 1
            elif opcode == OP_EQ:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a == b else 0)
                self.pc += 1
            elif opcode == OP_LT:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a < b else 0)
                self.pc += 1
            elif opcode == OP_HALT:
                break
            else:
                raise ValueError(f"Opcode desconhecido: {opcode} no PC={self.pc}")

# Programa em Bytecode para calcular o Fatorial de 5
# Algoritmo em pseudocódigo:
# result = 1
# n = 5
# while n > 1:
#     result = result * n
#     n = n - 1
factorial_bytecode = [
    (OP_PUSH, 1),   # 0: result = 1
    (OP_STORE, 'result'),
    (OP_PUSH, 5),   # 2: n = 5
    (OP_STORE, 'n'),
    # Loop Start (PC: 4)
    (OP_LOAD, 'n'), # 4: carrega n
    (OP_PUSH, 1),   # 5: carrega 1
    (OP_LT,        # 6: n < 1 ? (Na verdade, queremos rodar enquanto n > 1, então testamos n <= 1 para sair)
    # Vamos ajustar a lógica para: while n > 1
    # Mais simples: verificar se n == 1 para sair, ou n > 1 para continuar.
]

# Refazendo o bytecode do fatorial de forma limpa e comentada:
# Variaveis: 'n' (argumento), 'res' (acumulador)
# n = 5
# res = 1
# [Loop Check]:
# se n <= 1, vai para o fim (HALT)
# res = res * n
# n = n - 1
# volta para [Loop Check]

factorial_program = [
    (OP_PUSH, 5),       # 0: n = 5
    (OP_STORE, 'n'),
    (OP_PUSH, 1),       # 2: res = 1
    (OP_STORE, 'res'),
    # --- INÍCIO DO LOOP (PC: 4) ---
    (OP_LOAD, 'n'),     # 4: carrega n
    (OP_PUSH, 1),       # 5: carrega 1
    (OP_EQ,             # 6: n == 1 ?
    (OP_JMPF, 11),      # 7: se falso (n != 1), continua o loop. Se verdadeiro (n == 1), pula para o fim (índice 11)
    (OP_JMP, 14),       # (Correção de índice abaixo para simplificar saltos)
]

# Vamos escrever uma sequência linear robusta de bytecode para o fatorial de 5:
# 0: PUSH 5
# 1: STORE 'n'
# 2: PUSH 1
# 3: STORE 'res'
# --- LOOP (PC 4) ---
# 4: LOAD 'n'
# 5: PUSH 1
# 6: LT          # (n < 1) -> Se n for 0 ou menor, sai. Mas queremos n > 1.
# Vamos usar a comparação exata:

factorial_bytecode_clean = [
    (OP_PUSH, 5),       # 0: n = 5
    (OP_STORE, 'n'),
    (OP_PUSH, 1),       # 2: res = 1
    (OP_STORE, 'res'),
    # [4] Início do loop
    (OP_LOAD, 'n'),     # 4: pilha = [n]
    (OP_PUSH, 1),       # 5: pilha = [n, 1]
    (OP_LT,             # 6: pilha = [n < 1] (0 ou 1)
    (OP_JMPF, 10),      # 7: Se n < 1 for Falso (0), pula para instrução 10 (corpo do loop). Se Verdadeiro (1), continua para sair.
    (OP_JMP, 19),       # 8: Sai do loop (vai para HALT no PC 19)
    # [10] Corpo do loop
    (OP_LOAD, 'res'),   # 10: pilha = [res]
    (OP_LOAD, 'n'),     # 11: pilha = [res, n]
    (OP_MUL,            # 12: pilha = [res * n]
    (OP_STORE, 'res'),  # 13: res = res * n
    (OP_LOAD, 'n'),     # 14: pilha = [n]
    (OP_PUSH, 1),       # 15: pilha = [n, 1]
    (OP_SUB,            # 16: pilha = [n - 1]
    (OP_STORE, 'n'),    # 17: n = n - 1
    (OP_JMP, 4),        # 18: Retorna ao início do loop
    # [19] Fim
    (OP_HALT, None)     # 19: Para
]

def test_factorial():
    vm = StackVM(factorial_bytecode_clean, debug=True)
    vm.run()
    # O resultado deve estar armazenado na variável local 'res'
    assert vm.locals['res'] == 120, f"Esperado 120, obtido {vm.locals['res']}"
    print(f"Sucesso! Fatorial de 5 calculado corretamente como: {vm.locals['res']}")

def test_arithmetic_operations():
    # Testa operações básicas isoladas: (10 + 5) * 2 - 4 / 2 = 30 - 2 = 28
    code = [
        (OP_PUSH, 10),
        (OP_PUSH, 5),
        (OP_ADD,),
        (OP_PUSH, 2),
        (OP_MUL,),
        (OP_PUSH, 4),
        (OP_PUSH, 2),
        (OP_DIV,),
        (OP_SUB,),
        (OP_HALT,)
    ]
    vm = StackVM(code)
    vm.run()
    assert vm.stack.pop() == 28

# Demonstração do Equívoco Comum combatido:
# Equívoco: Confundir pilha de execução/dados com dados estáticos ou estrutura de pilha errada.
def test_counter_example_wrong_stack_ops():
    """
    Demonstração de por que a ordem dos operandos na pilha importa (Ordem LIFO).
    Em OP_SUB (a - b), o topo da pilha é 'b' e o abaixo é 'a'.
    Se invertido ou tratado como pilha de dados genérica sem respeitar a semântica, o resultado falha.
    """
    # Queremos calcular 5 - 3 (esperado: 2).
    # Se empurramos 5 e depois 3: topo é 3, abaixo é 5. Subtração faz a - b = 5 - 3 = 2.
    code_correct = [
        (OP_PUSH, 5),
        (OP_PUSH, 3),
        (OP_SUB,),
        (OP_HALT,)
    ]
    vm = StackVM(code_correct)
    vm.run()
    assert vm.stack.pop() == 2

    # Se a ordem for invertida incorretamente: 3 - 5 = -2
    code_wrong = [
        (OP_PUSH, 3),
        (OP_PUSH, 5),
        (OP_SUB,),
        (OP_HALT,)
    ]
    vm2 = StackVM(code_wrong)
    vm2.run()
    result_wrong = vm2.stack.pop()
    assert result_wrong == -2 # Mostra que a ordem LIFO afeta diretamente o resultado aritmético.