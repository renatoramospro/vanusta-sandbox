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

    def run(self, initial_val=0, iterations=1):
        total_acc = 0
        for _ in range(iterations):
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
                    break
                else:
                    raise ValueError(f"Opcode desconhecido: {op}")
            total_acc = acc
        return total_acc

class JITCompiler:
    def __init__(self, code):
        self.code = code
        self.machine_code = self._compile(code)
        self.executable_mem = self._allocate_executable_memory(self.machine_code)
        self.func = self._bind_function(self.executable_mem)

    def _compile(self, code):
        """
        Compila o bytecode e insere um loop nativo em x86_64 utilizando o registrador ECX
        como contador de iterações para eliminar o overhead de chamadas repetidas via ctypes.
        
        Convenção de chamada System V AMD64 ABI (Linux/Unix):
        - O primeiro argumento (iterations) vem em RDI (ou EDI).
        Vamos mover o argumento de contagem de RDI para ECX e executar o loop em assembly.
        """
        machine_code = bytearray()
        
        # 1. Salvar registradores se necessário e mover o argumento de iterações (EDI) para ECX
        # mov ecx, edi  (opcode: 89 f9)
        machine_code.extend(b'\x89\xf9')
        
        # 2. Inicializar acumulador EAX = 0 (xor eax, eax -> 31 c0)
        machine_code.extend(b'\x31\xc0')
        
        # Início do loop nativo (Label Loop_Start)
        # Offset para o salto condicional (será calculado ou mantido fixo para este benchmark)
        # Vamos construir o corpo do loop diretamente:
        loop_body_offset = len(machine_code)
        
        # Traduz o bytecode original dentro do corpo do loop
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
                pc += 1
            else:
                raise ValueError(f"Opcode JIT desconhecido: {op}")

        # Decrementa ECX e pula para o início se não for zero:
        # dec ecx (49 ff c9 ou 83 c9 ... -> dec ecx em 64-bit é ff c9 com rex.w ou 48 ff c9)
        # Mais simples: dec ecx (48 ff c9) ou usar ecx diretamente: 83 e9 01 (sub ecx, 1) e jnz loop_start
        
        # sub ecx, 1 (83 e9 01)
        machine_code.extend(b'\x83\xe9\x01')
        
        # jnz relative_offset
        # Precisamos calcular o salto relativo de volta para loop_body_offset
        current_pos_after_jnz = len(machine_code) + 2 # +2 do jnz (opcode 75 + rel8)
        rel_offset = loop_body_offset - current_pos_after_jnz
        
        machine_code.extend(b'\x75') # jnz rel8
        machine_code.append(rel_offset & 0xff)

        # Retorno (ret -> c3)
        machine_code.extend(b'\xc3')
        return bytes(machine_code)

    def _allocate_executable_memory(self, code):
        mem = mmap.mmap(-1, len(code), mmap.MAP_PRIVATE, mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        mem.write(code)
        return mem

    def _bind_function(self, mem):
        # A função nativa agora aceita 1 argumento inteiro (iterations) e retorna o acumulador em EAX
        func_type = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)
        return func_type(ctypes.addressof(ctypes.c_char.from_buffer(mem)))

    def run(self, iterations=1):
        return self.func(iterations)

def benchmark():
    # Bytecode de cálculo intensivo:
    # LOAD 5
    # ADD 10
    # MUL 2
    # SUB 3
    # RET
    code = [
        OP_LOAD, 5,
        OP_ADD, 10,
        OP_MUL, 2,
        OP_SUB, 3,
        OP_RET
    ]

    iterations = 1_000_000

    interp = Interpreter(code)
    jit = JITCompiler(code)

    # Medição Interpretador
    start = time.perf_counter()
    res_interp = interp.run(initial_val=0, iterations=iterations)
    time_interp = time.perf_counter() - start

    # Medição JIT (O loop inteiro roda dentro do código de máquina nativo!)
    start = time.perf_counter()
    res_jit = jit.run(iterations=iterations)
    time_jit = time.perf_counter() - start

    print(f"Resultado Interpretador: {res_interp} em {time_interp:.6f}s")
    print(f"Resultado JIT: {res_jit} em {time_jit:.6f}s")
    
    speedup = time_interp / time_jit if time_jit > 0 else 0
    print(f"Speedup obtido: {speedup:.2f}x")

    assert res_interp == res_jit, f"Resultados divergentes: {res_interp} != {res_jit}"
    assert speedup >= 5.0, f"Critério de sucesso não atingido: speedup de {speedup:.2f}x (esperado >= 5x)"
    print("Sucesso: O JIT superou o critério de 5x de velocidade com loop nativo em x86_64!")

if __name__ == "__main__":
    benchmark()