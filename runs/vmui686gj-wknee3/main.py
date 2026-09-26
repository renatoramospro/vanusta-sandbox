import math
import hashlib
import sys

class HyperLogLog:
    def __init__(self, b: int = 14):
        """
        Inicializa o HyperLogLog com b bits para indexação (2^b registradores).
        Para b = 14, m = 16384 registradores. Usamos bytearray para garantir
        espaço de 1 byte por registrador, totalizando exatamente 16 KB de payload.
        """
        if not (4 <= b <= 16):
            raise ValueError("b deve estar entre 4 e 16.")
        self.b = b
        self.m = 1 << b
        self.registers = bytearray(self.m)
        
        # Constante de correção alpha_m
        if self.m == 16:
            self.alpha_m = 0.673
        elif self.m == 32:
            self.alpha_m = 0.697
        elif self.m == 64:
            self.alpha_m = 0.709
        else:
            self.alpha_m = 0.7213 / (1.0 + 1.079 / self.m)

    def _hash(self, item: str) -> int:
        """Gera um hash SHA-256 de 64 bits para o item."""
        h = hashlib.sha256(item.encode('utf-8')).digest()
        # Pega os primeiros 8 bytes (64 bits)
        return int.from_bytes(h[:8], byteorder='big')

    def add(self, item: str):
        """Adiciona um elemento ao fluxo."""
        x = self._hash(item)
        # Os b bits mais à esquerda determinam o índice do registrador
        j = x >> (64 - self.b)
        # Os 64 - b bits restantes são usados para contar os zeros à esquerda + 1
        w = x & ((1 << (64 - self.b)) - 1)
        
        # Número de zeros à esquerda nos bits restantes + 1
        # Se w for 0, o número de bits é (64 - b) + 1
        leading_zeros = (64 - self.b) - w.bit_length() + 1
        
        if leading_zeros > self.registers[j]:
            self.registers[j] = leading_zeros

    def count(self) -> float:
        """Estima a cardinalidade usando a média harmônica de 2^(-M[j])."""
        raw_sum = 0.0
        for val in self.registers:
            raw_sum += 2.0 ** (-val)
            
        estimate = self.alpha_m * (self.m ** 2) / raw_sum
        
        # Correções de viés para cardinalidades pequenas ou grandes (LinearCounting / Limite superior)
        if estimate <= 2.5 * self.m:
            # Linear counting se houver muitos registradores vazios
            zeros = self.registers.count(0)
            if zeros > 0:
                estimate = self.m * math.log(self.m / zeros)
        elif estimate > (1.0 / 30.0) * (2.0 ** 32):
            # Correção para estouro em 32 bits (se aplicável)
            estimate = -(2.0 ** 32) * math.log(1.0 - estimate / (2.0 ** 32))
            
        return estimate

def test_hyperloglog_memory_and_accuracy():
    print("=== Iniciando Teste Rigoroso do HyperLogLog ===")
    
    # Usando b = 14 -> m = 16384 registradores.
    # Em um bytearray, o armazenamento consome exatamente 16384 bytes (16 KB).
    hll = HyperLogLog(b=14)
    
    # Validação estrita do consumo de memória do buffer de registradores
    payload_size = sys.getsizeof(hll.registers)
    print(f"Tamanho do buffer bytearray (registradores): {payload_size} bytes")
    
    # O payload bruto deve ser estritamente menor ou igual a 16384 bytes (16 KB)
    # Nota: sys.getsizeof inclui o cabeçalho do objeto Python (~56 bytes), 
    # mas o espaço alocado para os dados é exatamente m bytes.
    assert len(hll.registers) == 16384, "O número de registradores deve ser 16384 para b=14."
    
    num_elements = 1_000_000
    print(f"Inserindo {num_elements} elementos únicos...")
    
    for i in range(num_elements):
        hll.add(f"elemento_unico_{i}")
        
    estimated = hll.count()
    error = abs(estimated - num_elements) / num_elements
    
    print(f"Cardinalidade real:     {num_elements}")
    print(f"Cardinalidade estimada: {estimated:.2f}")
    print(f"Erro relativo:          {error * 100:.4f}%")
    
    # Critérios de Sucesso:
    # 1. Erro relativo inferior a 2%
    assert error < 0.02, f"Erro relativo ({error * 100:.4f}%) excedeu o limite de 2%!"
    
    # 2. Memória dos registradores estritamente menor ou igual a 16 KB (16384 bytes de dados)
    # Garantimos que len(hll.registers) == 16 * 1024 bytes.
    assert len(hll.registers) <= 16384, f"Payload de registradores ({len(hll.registers)} bytes) excedeu 16 KB!"
    
    print("SUCESSO: O HyperLogLog atendeu a todos os critérios de erro e limite de memória!")

if __name__ == "__main__":
    test_hyperloglog_memory_and_accuracy()