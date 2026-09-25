"""
StackVM - Máquina Virtual Baseada em Pilha (Versão Educacional Segura)
----------------------------------------------------------------------
AVISO DE SEGURANÇA (Conforme feedback da equipe de Segurança):
Esta implementação é um interpretador educacional projetado para executar 
bytecode estático, confiável e gerado internamente. 

NÃO A UTILIZE como sandbox para bytecode não confiável ou oriundo de usuários externos,
pois ela deliberadamente omite salvaguardas pesadas de produção, tais como:
1. Limitação de recursos (sem contador de instruções / 'gas' para evitar laços infinitos).
2. Validação estricta prévia do bytecode (risco de saltos inválidos, operandos ausentes ou malformados).
3. Isolamento de memória ou verificação rigorosa de tipos estáticos em tempo de execução.
"""

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
    """
    Interpretador de bytecode baseado em pilha.
    Assume que o bytecode de entrada é seguro e confiável (escrito pelo desenvolvedor).
    """
    def __init__(self, code, debug=False, max_instructions=100000):
        self.code = code
        self.pc = 0
        self.stack = []
        self.locals = {}
        self.debug = debug
        # Mitigação básica educacional: limite máximo de instruções para evitar loops infinitos locais
        self.max_instructions = max_instructions

    def run(self):
        instruction_count = 0
        while self.pc < len(self.code):
            instruction_count += 1
            if instruction_count > self.max_instructions:
                raise RuntimeError("Erro de Segurança/Execução: Limite máximo de instruções excedido (possível loop infinito).")

            instruction = self.code[self.pc]
            op = instruction[0]
            
            if self.debug:
                print(f"PC: {self.pc} | Op: {op} | Stack: {self.stack} | Locals: {self.locals}")

            if op == OP_PUSH:
                self.stack.append(instruction[1])
                self.pc += 1
            elif op == OP_POP:
                if not self.stack:
                    raise IndexError("Pilha vazia ao tentar executar OP_POP")
                self.stack.pop()
                self.pc += 1
            elif op == OP_ADD:
                if len(self.stack) < 2:
                    raise IndexError("Operandos insuficientes na pilha para OP_ADD")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
                self.pc += 1
            elif op == OP_SUB:
                if len(self.stack) < 2:
                    raise IndexError("Operandos insuficientes na pilha para OP_SUB")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)
                self.pc += 1
            elif op == OP_MUL:
                if len(self.stack) < 2:
                    raise IndexError("Operandos insuficientes na pilha para OP_MUL")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
                self.pc += 1
            elif op == OP_DIV:
                if len(self.stack) < 2:
                    raise IndexError("Operandos insuficientes na pilha para OP_DIV")
                b = self.stack.pop()
                if b == 0:
                    raise ZeroDivisionError("Divisão por zero detectada na máquina virtual")
                a = self.stack.pop()
                self.stack.append(a // b)
                self.pc += 1
            elif op == OP_LOAD:
                var_name = instruction[1]
                if var_name not in self.locals:
                    # Inicializa com 0 por segurança didática se não existir
                    self.locals[var_name] = 0
                self.stack.append(self.locals[var_name])
                self.pc += 1
            elif op == OP_STORE:
                if not self.stack:
                    raise IndexError("Pilha vazia ao tentar executar OP_STORE")
                var_name = instruction[1]
                self.locals[var_name] = self.stack.pop()
                self.pc += 1
            elif op == OP_JMP:
                target = instruction[1]
                if target < 0 or target >= len(self.code):
                    raise ValueError(f"Salto inválido (JMP) para o endereço {target}")
                self.pc = target
            elif op == OP_JMPF:
                if not self.stack:
                    raise IndexError("Pilha vazia ao tentar executar OP_JMPF")
                condition = self.stack.pop()
                target = instruction[1]
                if target < 0 or target >= len(self.code):
                    raise ValueError(f"Salto inválido (JMPF) para o endereço {target}")
                if not condition:
                    self.pc = target
                else:
                    self.pc += 1
            elif op == OP_EQ:
                if len(self.stack) < 2:
                    raise IndexError("Operandos insuficientes na pilha para OP_EQ")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a == b else 0)
                self.pc += 1
            elif op == OP_LT:
                if len(self.stack) < 2:
                    raise IndexError("Operandos insuficientes na pilha para OP_LT")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(1 if a < b else 0)
                self.pc += 1
            elif op == OP_HALT:
                break
            else:
                raise ValueError(f"Opcode desconhecido: {op}")

def test_factorial():
    """Programa em bytecode para calcular 5! = 120"""
    clean_fact_code = [
        (OP_PUSH, 5),       # 0: n = 5
        (OP_STORE, 'n'),    # 1
        (OP_PUSH, 1),       # 2: result = 1
        (OP_STORE, 'result'),# 3
        # PC 4: Início do loop
        (OP_LOAD, 'n'),     # 4
        (OP_PUSH, 0),       # 5
        (OP_EQ,),           # 6
        (OP_JMPF, 10),      # 7 -> se n != 0, pula para corpo (10)
        (OP_JMP, 19),       # 8 -> se n == 0, pula para fim (19)
        (OP_PUSH, 0),       # 9: no-op placeholder
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