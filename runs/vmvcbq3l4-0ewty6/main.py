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
        self._validate_bytecode(code)
        self.code = code

    def _validate_bytecode(self, code):
        if not isinstance(code, list):
            raise TypeError("Bytecode deve ser uma lista")
        pc = 0
        n = len(code)
        while pc < n:
            op = code[pc]
            if op in (OP_LOAD, OP_ADD, OP_SUB, OP_MUL):
                if pc + 1 >= n:
                    raise ValueError(f"Opcode {op} requer um operando, mas atingiu o fim do bytecode.")
                operand = code[pc + 1]
                # Validação de limites para evitar overflows arbitrários (-2^31 a 2^31 - 1)
                if not isinstance(operand, int) or not (-2147483648 <= operand <= 2147483647):
                    raise ValueError(f"Operando fora dos limites seguros de 32-bit: {operand}")
                pc += 2
            elif op == OP_RET:
                pc += 1
            else:
                raise ValueError(f"Opcode desconhecido ou malicioso: {op}")

    def run(self, initial_val=0, iterations=1):
        if not isinstance(iterations, int) or iterations < 0:
            raise ValueError("Número de iterações inválido")
        
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
                    # Mitigação de overflow simulado em Python (mantém em 32-bit signed)
                    acc &= 0xFFFFFFFF
                    if acc & 0x80000000:
                        acc -= 0x100000000
                    pc += 2
                elif op == OP_RET:
                    break
                else:
                    raise ValueError(f"Opcode desconhecido: {op}")
            total_acc = acc
        return total_acc

class JITCompiler:
    def __init__(self, code):
        # Validação robusta contra bytecode malicioso antes da compilação
        self._validate_bytecode(code)
        self.code = code
        self.machine_code = self._compile(code)
        self.executable_mem = self._allocate_executable_memory(self.machine_code)
        self.func = self._bind_function(self.executable_mem)

    def _validate_bytecode(self, code):
        # Reutiliza a mesma validação rigorosa do interpretador
        Interpreter(code)

    def _compile(self, code):
        # Montador x86_64 aprimorado com loop nativo (ECX) e validações embutidas
        # Convenção de chamada System V AMD64 ABI: 1º argumento em EDI (iterations)
        # Retorno em EAX (acumulador)
        
        machine_code = bytearray()

        # 1. Copiar argumento de iterações (EDI) para ECX (contador do loop nativo)
        machine_code.extend(b'\x89\xf9')  # mov ecx, edi

        # 2. Inicializar acumulador EAX com 0
        machine_code.extend(b'\x31\xc0')  # xor eax, eax

        # Início do Loop (rótulo l_start)
        loop_start_offset = len(machine_code)

        pc = 0
        n = len(code)
        while pc < n:
            op = code[pc]
            if op == OP_LOAD:
                val = code[pc + 1] & 0xFFFFFFFF
                # mov eax, imm32 -> b8 [imm32 little endian]
                machine_code.append(0xB8)
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=False))
                pc += 2
            elif op == OP_ADD:
                val = code[pc + 1] & 0xFFFFFFFF
                # add eax, imm32 -> 05 [imm32 little endian]
                machine_code.append(0x05)
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=False))
                pc += 2
            elif op == OP_SUB:
                val = code[pc + 1] & 0xFFFFFFFF
                # sub eax, imm32 -> 2d [imm32 little endian]
                machine_code.append(0x2D)
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=False))
                pc += 2
            elif op == OP_MUL:
                val = code[pc + 1] & 0xFFFFFFFF
                # imul eax, eax, imm32 -> 69 c0 [imm32 little endian]
                machine_code.extend(b'\x69\xC0')
                machine_code.extend(val.to_bytes(4, byteorder='little', signed=False))
                pc += 2
            elif op == OP_RET:
                pc += 1
            else:
                raise ValueError(f"Opcode não suportado no JIT: {op}")

        # Decrementar ECX e saltar se não for zero (dec ecx; jnz loop_start)
        # dec ecx -> ff c9 (ou 49 ff c1 dependendo do registrador, mas em 32/64 bit: 49 c9 ou 83 c9 ... dec ecx nativo: b9 / dec é 49 c9 em REX ou 41 c9. Vamos usar o padrão x86: 49 c9 ou dec ecx tradicional: 48 ff c9 / ff c9)
        # Correção para dec ecx em x86_64: 48 ff c9 decrementa rcx, mas para ecx puro: 83 c9 ... o opcode correto para dec ecx é \xff\xc9
        machine_code.extend(b'\xFF\xC9')  # dec ecx
        
        # jnz relative_offset
        # Calcula o salto relativo de volta para loop_start_offset
        current_offset_after_jnz = len(machine_code) + 2
        rel_offset = loop_start_offset - current_offset_after_jnz
        machine_code.append(0x75)  # jnz rel8
        machine_code.append(rel_offset & 0xFF)

        # Retornar (ret)
        machine_code.append(0xC3)

        return bytes(machine_code)

    def _allocate_executable_memory(self, machine_code):
        mem_size = max(len(machine_code), 4096)
        mem = mmap.mmap(-1, mem_size, prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        mem[:len(machine_code)] = machine_code
        return mem

    def _bind_function(self, mem):
        func_type = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)
        return func_type(ctypes.addressof(ctypes.c_char.from_buffer(mem)))

    def run(self, iterations=1):
        if not isinstance(iterations, int) or iterations < 0:
            raise ValueError("Número de iterações inválido")
        return self.func(iterations)

def benchmark():
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

    # Medição JIT
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

def test_adversarial_and_edge_cases():
    print("\n--- Executando Testes Adversariais e de Segurança ---")
    
    # 1. Teste de Opcode Desconhecido / Malicioso
    malicious_code = [OP_LOAD, 5, 99, 0, OP_RET] # 99 é inválido
    try:
        Interpreter(malicious_code)
        raise AssertionError("Deveria ter falhado com opcode malicioso no Interpretador")
    except ValueError as e:
        print(f"[Segurança OK] Interpretador bloqueou bytecode malicioso: {e}")

    try:
        JITCompiler(malicious_code)
        raise AssertionError("Deveria ter falhado com opcode malicioso no JIT")
    except ValueError as e:
        print(f"[Segurança OK] JIT Compiler bloqueou bytecode malicioso: {e}")

    # 2. Teste de Operando Fora de Limites (Overflow attempt)
    overflow_code = [OP_LOAD, 9999999999999999, OP_RET]
    try:
        JITCompiler(overflow_code)
        raise AssertionError("Deveria ter falhado com operando fora dos limites")
    except ValueError as e:
        print(f"[Segurança OK] Validação de limites impediu estouro de operando: {e}")

    print("Todos os testes adversariais passaram com sucesso!")

if __name__ == "__main__":
    benchmark()
    test_adversarial_and_edge_cases()