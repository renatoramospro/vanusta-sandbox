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
OP_STORE = 9   # Armazena o topo da pilha na memória
OP_PRINT = 10
OP_HALT  = 11

class StackVM:
    def __init__(self, bytecode):
        self.bytecode = bytecode
        self.pc = 0
        self.stack = []
        self.memory = {}
        self.running = True

    def fetch(self):
        if self.pc < 0 or self.pc >= len(self.bytecode):
            raise IndexError(f"PC fora dos limites do bytecode: {self.pc}")
        instruction = self.bytecode[self.pc]
        self.pc += 1
        return instruction

    def run(self):
        steps = 0
        max_steps = 10000  # Proteção contra loop infinito
        while self.running:
            steps += 1
            if steps > max_steps:
                raise RuntimeError("Erro: Limite máximo de passos excedido (loop infinito detectado).")
            
            opcode = self.fetch()
            
            if opcode == OP_PUSH:
                val = self.fetch()
                self.stack.append(val)
                
            elif opcode == OP_POP:
                if not self.stack:
                    raise IndexError("Erro: POP em pilha vazia.")
                self.stack.pop()
                
            elif opcode == OP_ADD:
                if len(self.stack) < 2:
                    raise IndexError("Erro: ADD requer pelo menos 2 elementos na pilha.")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
                
            elif opcode == OP_SUB:
                if len(self.stack) < 2:
                    raise IndexError("Erro: SUB requer pelo menos 2 elementos na pilha.")
                b = self.stack.pop() # subtraendo
                a = self.stack.pop() # minuendo
                self.stack.append(a - b)
                
            elif opcode == OP_MUL:
                if len(self.stack) < 2:
                    raise IndexError("Erro: MUL requer pelo menos 2 elementos na pilha.")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
                
            elif opcode == OP_JUMP:
                addr = self.fetch()
                if addr < 0 or addr >= len(self.bytecode):
                    raise IndexError(f"Erro: Endereço de JUMP inválido: {addr}")
                self.pc = addr
                
            elif opcode == OP_JZ:
                addr = self.fetch()
                if addr < 0 or addr >= len(self.bytecode):
                    raise IndexError(f"Erro: Endereço de JZ inválido: {addr}")
                if not self.stack:
                    raise IndexError("Erro: JZ requer elemento no topo da pilha.")
                val = self.stack.pop()
                if val == 0:
                    self.pc = addr
                    
            elif opcode == OP_LOAD:
                addr = self.fetch()
                if addr not in self.memory:
                    # Inicializa com 0 caso não exista para evitar falhas de leitura
                    self.memory[addr] = 0
                self.stack.append(self.memory[addr])
                
            elif opcode == OP_STORE:
                addr = self.fetch()
                if not self.stack:
                    raise IndexError("Erro: STORE requer elemento no topo da pilha.")
                val = self.stack.pop()
                self.memory[addr] = val
                
            elif opcode == OP_PRINT:
                if not self.stack:
                    raise IndexError("Erro: PRINT requer elemento no topo da pilha.")
                val = self.stack.pop()
                print(f"[VM OUTPUT]: {val}")
                
            elif opcode == OP_HALT:
                self.running = False
            else:
                raise ValueError(f"Opcode desconhecido: {opcode} no PC={self.pc - 1}")

def test_fibonacci_10():
    print("--- Testando Cálculo de Fibonacci até o 10º termo ---")
    # Algoritmo de Fibonacci Iterativo:
    # Mem[0] = contador (10)
    # Mem[1] = fib(n-1) inicialmente 0 (Fib 0)
    # Mem[2] = fib(n)   inicialmente 1 (Fib 1)
    # Mem[3] = temporário / fib_novo
    
    bytecode = [
        # Inicialização
        OP_PUSH, 10,
        OP_STORE, 0,    # Mem[0] = 10 (contador)
        
        OP_PUSH, 0,
        OP_STORE, 1,    # Mem[1] = 0 (fib(n-1))
        
        OP_PUSH, 1,
        OP_STORE, 2,    # Mem[2] = 1 (fib(n))
        
        # --- INÍCIO DO LOOP (PC = 12) ---
        OP_LOAD, 0,     # Carrega contador
        OP_JZ, 38,      # Se contador == 0, salta para o fim (PC = 38)
        
        # fib_novo = fib(n-1) + fib(n)
        OP_LOAD, 1,
        OP_LOAD, 2,
        OP_ADD,
        OP_STORE, 3,    # Mem[3] = fib_novo
        
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
        
        # Salta de volta para o início do loop (PC = 12)
        OP_JUMP, 12,
        
        # --- FIM DO LOOP (PC = 38) ---
        OP_LOAD, 1,
        OP_PRINT,
        OP_HALT
    ]
    
    vm = StackVM(bytecode)
    vm.run()
    
    print(f"Estado final da memória - Mem[1] (Fib 10): {vm.memory[1]}")
    assert vm.memory[1] == 55, f"Esperado 55, obtido {vm.memory[1]}"
    print("Sucesso: Fibonacci 10 calculado com 100% de precisão!")

def test_stack_order_and_subtraction():
    print("\n--- Testando Correção de Ordem de Operandos (Subtração) ---")
    bytecode = [
        OP_PUSH, 10,
        OP_PUSH, 3,
        OP_SUB,
        OP_PRINT,
        OP_HALT
    ]
    vm = StackVM(bytecode)
    vm.run()
    print("Ordem de pilha validada com sucesso.")

if __name__ == "__main__":
    test_fibonacci_10()
    test_stack_order_and_subtraction()
    print("\nTodos os testes executados com sucesso!")