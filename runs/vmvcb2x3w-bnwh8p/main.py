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
        self.machine_code = self._compile(code)
        self.executable_mem = self._allocate_executable_memory(self.machine_code)
        self.func = self._bind_function(self.executable_mem)

    def _compile(self, code):
        # Tradução simples de bytecode para x86_64 machine code
        # x86_64 opcodes:
        # mov eax, imm32 -> b8 [imm32 little-endian]
        # add eax, imm32 -> 05 [imm32 little-endian]
        # sub eax, imm32 -> 2d [imm32 little-endian]
        # imul eax, eax, imm32 -> 69 c0 [imm32 little-endian]
        # ret -> c3
        
        machine_code = bytearray()
        pc = 0
        n = len(code)
        while pc < n:
            op = code[pc]
            if op == OP_LOAD:
                val = code[pc + 1]
                machine_code.extend(b'\xb8') # mov eax, imm32
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_ADD:
                val = code[pc + 1]
                machine_code.extend(b'\x05') # add eax, imm32
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_SUB:
                val = code[pc + 1]
                machine_code.extend(b'\x2d') # sub eax, imm32
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_MUL:
                val = code[pc + 1]
                machine_code.extend(b'\x69\xc0') # imul eax, eax, imm32
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=True))
                pc += 2
            elif op == OP_RET:
                machine_code.extend(b'\xc3') # ret
                pc += 1
            else:
                raise ValueError(f"Opcode JIT desconhecido: {op}")
        return bytes(machine_code)

    def _allocate_executable_memory(self, code):
        # Aloca memória com permissões de leitura, escrita e execução (RWX)
        # Necessário em plataformas modernas (respeitando restrições de DEP/NX)
        mem = mmap.mmap(-1, len(code), prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        mem.write(code)
        return mem

    def _bind_function(self, mem):
        # Utiliza ctypes para vincular o buffer de memória executável a uma função C chamável
        buf_addr = ctypes.addressof(ctypes.c_char.from_buffer(mem))
        # Assinatura: int func(void)
        func_type = ctypes.CFUNCTYPE(ctypes.c_int32)
        return func_type(buf_addr)

    def run(self, initial_val=0):
        # Nota: O bytecode gerado inicializa EAX diretamente via LOAD_CONST, 
        # ignorando initial_val para manter a simplicidade do protótipo x86_64.
        return self.func()

def benchmark():
    # Programa de teste: ((10 + 5) * 2) - 3 = 27
    bytecode = [
        OP_LOAD, 10,
        OP_ADD,   5,
        OP_MUL,   2,
        OP_SUB,   3,
        OP_RET
    ]

    interp = Interpreter(bytecode)
    jit = JITCompiler(bytecode)

    iterations = 100_000

    # Medição Interpretador
    start = time.perf_counter()
    res_interp = 0
    for _ in range(iterations):
        res_interp = interp.run()
    time_interp = time.perf_counter() - start

    # Medição JIT
    start = time.perf_counter()
    res_jit = 0
    for _ in range(iterations):
        res_jit = jit.run()
    time_jit = time.perf_counter() - start

    print(f"Resultado Interpretador: {res_interp} em {time_interp:.6f}s")
    print(f"Resultado JIT: {res_jit} em {time_jit:.6f}s")
    
    speedup = time_interp / time_jit if time_jit > 0 else 0
    print(f"Speedup obtido: {speedup:.2f}x")

    assert res_interp == res_jit, f"Resultados divergentes: {res_interp} != {res_jit}"
    assert speedup >= 5.0, f"Critério de sucesso não atingido: speedup de {speedup:.2f}x (esperado >= 5x)"
    print("Sucesso: O JIT superou o critério de 5x de velocidade!")

if __name__ == "__main__":
    benchmark()