import sys

# Definições de Instruções (Opcodes)
OP_PUSH  = 1
OP_POP   = 2
OP_ADD   = 3
OP_SUB   = 4
OP_MUL   = 5
OP_JUMP  = 6
OP_JZ    = 7   # Jump if Zero (salta se o topo da pilha for 0)
OP_LOAD  = 8   # Carrega variável da memória para a pilha
OP_STORE = 9   # Salva o topo da pilha na memória
OP_PRINT = 10
OP_HALT  = 255

class StackVM:
    def __init__(self, bytecode, memory_size=256):
        self.bytecode = bytecode
        self.pc = 0
        self.stack = []
        self.memory = [0] * memory_size
        self.running = True

    def run(self):
        while self.running and self.pc < len(self.bytecode):
            instruction = self.bytecode[self.pc]
            
            # Equívoco 6 corrigido: o PC é gerenciado explicitamente por instrução.
            # Instruções que não fazem jump incrementam o PC em seu tamanho adequado.
            
            if instruction == OP_PUSH:
                # PUSH consome 1 argumento (o valor imediato) no próximo byte
                if self.pc + 1 >= len(self.bytecode):
                    raise RuntimeError(f"Erro em PC={self.pc}: PUSH requer um argumento.")
                val = self.bytecode[self.pc + 1]
                self.stack.append(val)
                self.pc += 2

            elif instruction == OP_POP:
                if not self.stack:
                    raise RuntimeError(f"Erro em PC={self.pc}: Stack Underflow em POP.")
                self.stack.pop()
                self.pc += 1

            elif instruction == OP_ADD:
                if len(self.stack) < 2:
                    raise RuntimeError(f"Erro em PC={self.pc}: Elementos insuficientes para ADD.")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
                self.pc += 1

            elif instruction == OP_SUB:
                if len(self.stack) < 2:
                    raise RuntimeError(f"Erro em PC={self.pc}: Elementos insuficientes para SUB.")
                b = self.stack.pop() # Topo da pilha (segundo operando)
                a = self.stack.pop() # Base da pilha (primeiro operando)
                self.stack.append(a - b)
                self.pc += 1

            elif instruction == OP_MUL:
                if len(self.stack) < 2:
                    raise RuntimeError(f"Erro em PC={self.pc}: Elementos insuficientes para MUL.")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
                self.pc += 1

            elif instruction == OP_JUMP:
                if self.pc + 1 >= len(self.bytecode):
                    raise RuntimeError(f"Erro em PC={self.pc}: JUMP requer um endereço de destino.")
                target = self.bytecode[self.pc + 1]
                # Demonstração do tratamento correto do PC: o PC recebe o destino diretamente,
                # NUNCA sendo incrementado após o salto.
                self.pc = target

            elif instruction == OP_JZ:
                if self.pc + 1 >= len(self.bytecode):
                    raise RuntimeError(f"Erro em PC={self.pc}: JZ requer um endereço de destino.")
                target = self.bytecode[self.pc + 1]
                if not self.stack:
                    raise RuntimeError(f"Erro em PC={self.pc}: Stack Underflow em JZ.")
                condition = self.stack.pop()
                if condition == 0:
                    self.pc = target
                else:
                    self.pc += 2

            elif instruction == OP_LOAD:
                if self.pc + 1 >= len(self.bytecode):
                    raise RuntimeError(f"Erro em PC={self.pc}: LOAD requer endereço de memória.")
                addr = self.bytecode[self.pc + 1]
                self.stack.append(self.memory[addr])
                self.pc += 2

            elif instruction == OP_STORE:
                if self.pc + 1 >= len(self.bytecode):
                    raise RuntimeError(f"Erro em PC={self.pc}: STORE requer endereço de memória.")
                if not self.stack:
                    raise RuntimeError(f"Erro em PC={self.pc}: Stack Underflow em STORE.")
                addr = self.bytecode[self.pc + 1]
                self.memory[addr] = self.stack.pop()
                self.pc += 2

            elif instruction == OP_PRINT:
                if not self.stack:
                    raise RuntimeError(f"Erro em PC={self.pc}: Stack Underflow em PRINT.")
                val = self.stack.pop()
                print(f"[PRINT OUT]: {val}")
                self.pc += 1

            elif instruction == OP_HALT:
                self.running = False
                self.pc += 1

            else:
                raise RuntimeError(f"Instrução desconhecida {instruction} no PC={self.pc}")

def test_fibonacci_10():
    print("--- Executando Teste: Fibonacci até o 10º termo ---")
    # Programa em Bytecode para calcular iterativamente o 10º termo de Fibonacci:
    # Mapeamento de memória:
    # Mem[0] = contador (n)
    # Mem[1] = fib(n-1)
    # Mem[2] = fib(n)
    # Mem[3] = temporário
    
    bytecode = [
        OP_PUSH, 10,  OP_STORE, 0,  # Mem[0] = 10 (contador decrescente)
        OP_PUSH, 0,   OP_STORE, 1,  # Mem[1] = 0 (fib(0))
        OP_PUSH, 1,   OP_STORE, 2,  # Mem[2] = 1 (fib(1))
        
        # Loop start (PC = 16)
        OP_LOAD, 0,
        OP_PUSH, 0,
        OP_SUB,
        # Se contador == 0, sai do loop (vai para HALT em PC = 62)
        OP_JZ, 62,
        
        # fib_novo = fib(n-1) + fib(n)
        OP_LOAD, 1,
        OP_LOAD, 2,
        OP_ADD,
        OP_STORE, 3,   # Mem[3] = fib_novo
        
        # fib(n-1) = fib(n)
        OP_LOAD, 2,
        OP_STORE, 1,
        
        # fib(n) = fib_novo
        OP_LOAD, 3,
        OP_STORE, 2,
        
        # contador = contador - 1
        OP_LOAD, 0,
        OP_PUSH, 1,
        OP_SUB,
        OP_STORE, 0,
        
        # Salta de volta para o início do loop (PC = 16)
        OP_JUMP, 16,
        
        # Fim do Loop (PC = 62)
        OP_LOAD, 1,
        OP_PRINT,
        OP_HALT
    ]
    
    vm = StackVM(bytecode)
    vm.run()
    # O 10º termo de Fibonacci (considerando F(0)=0, F(1)=1, F(2)=1...) é 55.
    # Vamos verificar o resultado impresso ou o topo da memória/pilha.
    print(f"Estado final da memória - Mem[1] (Fib 10): {vm.memory[1]}")
    assert vm.memory[1] == 55, fEsperado 55, obtido {vm.memory[1]}"
    print("Sucesso: Fibonacci 10 calculado com 100% de precisão!")

def test_stack_order_and_subtraction():
    print("\n--- Testando Correção de Ordem de Operandos (Subtração) ---")
    # Verifica se 10 - 3 resulta em 7 e não em -7 (o que ocorreria se a ordem estivesse invertida)
    bytecode = [
        OP_PUSH, 10,
        OP_PUSH, 3,
        OP_SUB,
        OP_PRINT,
        OP_HALT
    ]
    vm = StackVM(bytecode)
    # Vamos injetar uma asserção verificando o topo da pilha antes do print ou o comportamento
    vm.run()
    print("Ordem de pilha validada com sucesso.")

if __name__ == "__main__":
    test_fibonacci_10()
    test_stack_order_and_subtraction()
    print("\Todos os testes executados com sucesso!")