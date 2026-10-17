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
        max_steps = 10000  # Proteção contra loop infinito para garantir que nunca ocorra timeout
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
                b = self.stack.pop()
                a = self.stack.pop()
                # Ordem correta: a - b (a foi empurrado antes de b)
                self.stack.append(a - b)
                
            elif opcode == OP_MUL:
                if len(self.stack) < 2:
                    raise IndexError("Erro: MUL requer pelo menos 2 elementos na pilha.")
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
                
            elif opcode == OP_JUMP:
                target = self.fetch()
                self.pc = target
                
            elif opcode == OP_JZ:
                target = self.fetch()
                if not self.stack:
                    raise IndexError("Erro: JZ requer elemento no topo da pilha.")
                val = self.stack.pop()
                if val == 0:
                    self.pc = target
                    
            elif opcode == OP_LOAD:
                addr = self.fetch()
                val = self.memory.get(addr, 0)
                self.stack.append(val)
                
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
                print(f"[VM OUT]: {val}")
                
            elif opcode == OP_HALT:
                self.running = False
            else:
                raise ValueError(f"Opcode desconhecido: {opcode} no PC={self.pc-1}")

def test_fibonacci_10():
    print("--- Testando Cálculo de Fibonacci até o 10º termo ---")
    # Programa de Fibonacci iterativo:
    # Mem[0] = contador (10)
    # Mem[1] = fib(n-1) (inicia em 0)
    # Mem[2] = fib(n) (inicia em 1)
    
    bytecode = [
        # 0: Inicializar contador = 10
        OP_PUSH, 10,
        OP_STORE, 0,
        
        # 2: Inicializar fib(n-1) = 0
        OP_PUSH, 0,
        OP_STORE, 1,
        
        # 4: Inicializar fib(n) = 1
        OP_PUSH, 1,
        OP_STORE, 2,
        
        # --- INÍCIO DO LOOP (PC = 6) ---
        # 6: Verificar se contador == 0
        OP_LOAD, 0,
        OP_JZ, 34,      # Se contador == 0, salta para o fim (PC = 34)
        
        # 8: fib_novo = fib(n-1) + fib(n)
        OP_LOAD, 1,
        OP_LOAD, 2,
        OP_ADD,
        OP_STORE, 3,    # Mem[3] = fib_novo
        
        # 16: fib(n-1) = fib(n)
        OP_LOAD, 2,
        OP_STORE, 1,
        
        # 20: fib(n) = fib_novo
        OP_LOAD, 3,
        OP_STORE, 2,
        
        # 24: contador = contador - 1
        OP_LOAD, 0,
        OP_PUSH, 1,
        OP_SUB,
        OP_STORE, 0,
        
        # 30: Salta de volta para o início do loop (PC = 6)
        OP_JUMP, 6,
        
        # --- FIM DO LOOP (PC = 34) ---
        # 34: Carrega Mem[1] (que conterá o 10º termo) e imprime/halt
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
    # Verifica se 10 - 3 resulta em 7 e não em -7
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