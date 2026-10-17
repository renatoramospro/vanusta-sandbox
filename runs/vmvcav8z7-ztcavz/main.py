path=jit_compiler.py
import mmap
import ctypes
import time

# Opcodes do Bytecode Simplificado
OP_LOAD  = 1  # Carrega valor literal em EAX
OP_ADD   = 2  # Adiciona valor literal a EAX
OP_SUB   = 3  # Subtrai valor literal de EAX
OP_MUL   = 4  # Multiplica EAX por valor literal
OP_RET   = 5  # Retorna EAX

class Interpreter:
    def __init__(self, code):
        self.code = code

    def run(self, initial_val=0):
        pc = 0
        acc = initial_val
        n = len(self.code)
        while pc < n:
            op = self.code[pc]
            if op == OP_LOAD:
                acc = self.code[pc + 1]
                pc += 2
            elif op == OP_ADD:
                acc += self.code[pc + 1]
                pc += 2
            elif op == OP_SUB:
                acc -= self.code[pc + 1]
                pc += 2
            elif op == OP_MUL:
                acc *= self.code[pc + 1]
                pc += 2
            elif op == OP_RET:
                return acc
            else:
                raise ValueError(f"Opcode desconhecido: {op}")
        return acc

class JITCompiler:
    def __init__(self, code):
        self.code = code
        self.machine_code = self._compile()
        self.exec_mem = self._allocate_executable_memory(self.machine_code)
        
        # Cria ponteiro de função em C usando ctypes
        func_type = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)
        self.func = func_type(ctypes.addressof(self.exec_mem))

    def _compile(self):
        # Traduz bytecode simplificado para x86_64 machine code
        # Prólogo padrão x86_64 (opcional para funções simples folha)
        # Usamos registrador EAX como acumulador e EDI como argumento inicial.
        # x86_64 ABI: 1º argumento inteiro em EDI. Retorno em EAX.
        
        machine_bytes = bytearray()
        
        # mov eax, edi (Move argumento de entrada para o acumulador)
        machine_bytes.extend(b'\x89\xf8')

        pc = 0
        n = len(self.code)
        while pc < n:
            op = self.code[pc]
            if op == OP_LOAD:
                val = self.code[pc + 1] & 0xFFFFFFFF
                # mov eax, imm32 -> b8 [val 4 bytes little endian]
                machine_bytes.append(0xB8)
                machine_bytes.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_ADD:
                val = self.code[pc + 1] & 0xFFFFFFFF
                # add eax, imm32 -> 05 [val 4 bytes little endian]
                machine_bytes.append(0x05)
                machine_bytes.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_SUB:
                val = self.code[pc + 1] & 0xFFFFFFFF
                # sub eax, imm32 -> 2d [val 4 bytes little endian]
                machine_bytes.append(0x2D)
                machine_bytes.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_MUL:
                val = self.code[pc + 1] & 0xFFFFFFFF
                # imul eax, eax, imm32 -> 69 c0 [val 4 bytes]
                machine_bytes.extend(b'\x69\xC0')
                machine_bytes.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_RET:
                # ret
                machine_bytes.append(0xC3)
                pc += 1
            else:
                raise ValueError(f"Opcode desconhecido no JIT: {op}")
        
        # Garante que termine com ret se faltar
        if machine_bytes[-1] != 0xC3:
            machine_bytes.append(0xC3)

        return bytes(machine_bytes)

    def _allocate_executable_memory(self, code_bytes):
        # Aloca memória com permissão de leitura, escrita e execução (RWX)
        # Nota: Em sistemas modernos com W^X estrito, aloca-se RW e depois muda para RX.
        size = max(len(code_bytes), 4096)
        mem = mmap.mmap(-1, size, prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        mem.write(code_bytes)
        return mem

    def run(self, initial_val=0):
        return self.func(initial_val)

def benchmark():
    # Programa de teste: acumulador executa uma série de operações aritméticas pesadas num loop
    # Bytecode equivalente a: ((x + 5) * 2 - 3) * 3
    bytecode = [
        OP_ADD, 5,
        OP_MUL, 2,
        OP_SUB, 3,
        OP_MUL, 3,
        OP_RET
    ]

    iterations = 2_000_000

    # 1. Teste do Interpretador
    interp = Interpreter(bytecode)
    start = time.perf_counter()
    res_interp = 0
    for _ in range(iterations):
        res_interp = interp.run(10)
    time_interp = time.perf_counter() - start

    # 2. Teste do JIT Compiler
    jit = JITCompiler(bytecode)
    start = time.perf_counter()
    res_jit = 0
    for _ in range(iterations):
        res_jit = jit.run(10)
    time_jit = time.perf_counter() - start

    print(f"Resultado Interpretador: {res_interp} em {time_interp:.4f}s")
    print(f"Resultado JIT: {res_jit} em {time_jit:.4f}s")
    
    speedup = time_interp / time_jit if time_jit > 0 else 0
    print(f"Speedup obtido: {speedup:.2f}x")

    assert res_interp == res_jit, f"Resultados divergentes: {res_interp} != {res_jit}"
    assert speedup >= 5.0, f"Critério de sucesso não atingido: speedup de {speedup:.2f}x (esperado >= 5x)"
    print("Sucesso: O JIT superou o critério de 5x de velocidade!")

if __name__ == "__main__":
    benchmark()