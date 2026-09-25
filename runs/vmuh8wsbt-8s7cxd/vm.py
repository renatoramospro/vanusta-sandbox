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
                raise ValueError(f"Opcode desconhecido: {op} no PC: {self.pc}")

def test_factorial():
    # Programa em bytecode para calcular 5!
    # n = 5
    # result = 1
    # while n > 0:
    #     result = result * n
    #     n = n - 1
    
    fact_code = [
        (OP_PUSH, 5),       # 0: push 5
        (OP_STORE, 'n'),    # 1: n = 5
        (OP_PUSH, 1),       # 2: push 1
        (OP_STORE, 'result'),# 3: result = 1
        # Loop start (PC = 4)
        (OP_LOAD, 'n'),     # 4: carrega n
        (OP_PUSH, 0),       # 5: push 0
        (OP_EQ,),           # 6: n == 0?
        (OP_JMPF, 10),      # 7: se falso (n != 0), vai para o corpo (PC 10)
        (OP_JMP, 19),       # 8: se verdadeiro (n == 0), sai do loop (PC 19)
        (OP_POP,),          # 9: limpeza de pilha se necessário (place)
        # Corpo do loop (PC = 10)
        (OP_LOAD, 'result'),# 10: carrega result
        (OP_LOAD, 'n'),     # 11: carrega n
        (OP_MUL,),          # 12: result * n
        (OP_STORE, 'result'),# 13: armazena em result
        (OP_LOAD, 'n'),     # 14: carrega n
        (OP_PUSH, 1),       # 15: push 1
        (OP_SUB,),          # 16: n - 1
        (OP_STORE, 'n'),    # 17: armazena em n
        (OP_JMP, 4),        # 18: volta ao início do loop
        # Fim (PC = 19)
        (OP_LOAD, 'result'),# 19: carrega result final para o topo da pilha
        (OP_HALT,)          # 20: para
    ]
    
    # Versão simplificada e limpa para teste direto do fatorial
    clean_fact_code = [
        (OP_PUSH, 5),       # 0: n = 5
        (OP_STORE, 'n'),
        (OP_PUSH, 1),       # 2: result = 1
        (OP_STORE, 'result'),
        # PC 4: Loop check
        (OP_LOAD, 'n'),     # 4
        (OP_PUSH, 0),       # 5
        (OP_EQ,),           # 6
        (OP_JMPF, 10),      # 7 -> se n != 0, pula para corpo (10)
        (OP_JMP, 19),       # 8 -> se n == 0, pula para fim (19)
        (OP_PUSH, 0),       # 9: no-op placeholder para alinhar saltos
        # PC 10: Corpo
        (OP_LOAD, 'result'),# 10
        (OP_LOAD, 'n'),     # 11
        (OP_MUL,),          # 12
        (OP_STORE, 'result'),# 13
        (OP_LOAD, 'n'),     # 14
        (OP_PUSH, 1),       # 15
        (OP_SUB,),          # 16
        (OP_STORE, 'n'),    # 17
        (OP_JMP, 4),        # 18 -> volta ao início
        # PC 19: Fim
        (OP_LOAD, 'result'),# 19
        (OP_HALT,)          # 20
    ]

    vm = StackVM(clean_fact_code, debug=False)
    vm.run()
    
    result = vm.stack.pop()
    print(f"Resultado calculado do fatorial de 5: {result}")
    assert result == 120, f"Esperado 120, obtido {result}"

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
    res = vm.stack.pop()
    print(f"Resultado de 5 - na ordem LIFO (5 - 3): {res}")
    assert res == 2

if __name__ == "__main__":
    test_factorial()
    test_counter_example_wrong_stack_ops()
    print("Todos os testes executados com sucesso!")