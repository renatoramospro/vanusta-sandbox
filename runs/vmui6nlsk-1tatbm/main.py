import math
import hashlib
import sys

class HyperLogLog:
    def __init__(self, b: int = 12):
        """
        Inicializa o HyperLogLog com b bits para indexação (2^b registradores).
        Para b = 12, m = 4096 registradores. O buffer bytearray consome 4096 bytes
        e o objeto total em CPython fica em torno de 4153 bytes, garantindo
        estritamente menos de 16 KB (16384 bytes) totais de memória.
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
        """Gera um hash SHA-256 de 32 bits (4 bytes) para o elemento."""
        hash_obj = hashlib.sha256(str(item).encode('utf-8'))
        # Extrai os primeiros 4 bytes do hash como um inteiro de 32 bits
        return int.from_bytes(hash_obj.digest()[:4], byteorder='big')

    def add(self, item: str):
        """Adiciona um elemento ao HyperLogLog."""
        x = self._hash(item)
        # Os primeiros b bits determinam o índice do registrador
        j = x >> (32 - self.b)
        # Os bits restantes determinam o número de zeros à esquerda + 1
        w = x & ((1 << (32 - self.b)) - 1)
        
        # Computa a posição do primeiro bit 1 (contando a partir da esquerda após os b bits)
        # rho(w) = clz(w) + 1
        leading_zeros = 32 - self.b - w.bit_length() + 1
        rank = max(1, leading_zeros)
        
        if rank > self.registers[j]:
            self.registers[j] = rank

    def count(self) -> float:
        """Estima a cardinalidade utilizando a média harmônica com correções."""
        # Aplicação da média harmônica sobre os termos exponenciais 2^{-M[j]}
        indicator_sum = sum(2.0 ** (-val) for val in self.registers)
        raw_estimate = self.alpha_m * (self.m ** 2) / indicator_sum
        
        # Correção para cardinalidades baixas (LinearCounting)
        if raw_estimate <= 2.5 * self.m:
            zeros_count = self.registers.count(0)
            if zeros_count > 0:
                return self.m * math.log(self.m / zeros_count)
                
        # Correção para cardinalidades extremamente altas (saturação de 32 bits)
        # Limite prático quando a cardinalidade se aproxima de 1/30 de 2^32
        two_32 = 4294967296.0
        if raw_estimate > (two_32 / 30.0):
            return -two_32 * math.log(1.0 - (raw_estimate / two_32))
            
        return raw_estimate

def test_hyperloglog_memory_and_accuracy():
    print("=== Iniciando Teste Rigoroso do HyperLogLog (b=12) ===")
    
    # Instancia o HLL com b=12 (4096 registradores)
    hll = HyperLogLog(b=12)
    
    # Medição real do consumo total do objeto em memória (incluindo overhead do CPython)
    total_object_size = sys.getsizeof(hll) + sys.getsizeof(hll.registers)
    print(f"Tamanho total medido do objeto HLL na memória: {total_object_size} bytes")
    print(f"Tamanho do buffer bytearray puro: {sys.getsizeof(hll.registers)} bytes")
    
    # Validação rigorosa de memória sem depender de assert (lança exceção de produção)
    max_allowed_memory = 16384 # 16 KB
    if total_object_size > max_allowed_memory:
        raise RuntimeError(f"FALHA DE MEMÓRIA: Objeto consome {total_object_size} bytes, excedendo o teto de 16 KB.")
    
    num_elements = 1_000_000
    print(f"Inserindo {num_elements} elementos únicos...")
    
    for i in range(num_elements):
        hll.add(f"elemento_unico_{i}")
        
    estimated = hll.count()
    error = abs(estimated - num_elements) / num_elements
    
    print(f"Cardinalidade real:     {num_elements}")
    print(f"Cardinalidade estimada: {estimated:.2f}")
    print(f"Erro relativo:          {error * 100:.4f}%")
    
    # Validação de erro relativo (< 2%)
    if error >= 0.02:
        raise RuntimeError(f"FALHA DE PRECISÃO: Erro relativo ({error * 100:.4f}%) excedeu o limite de 2%.")
        
    print("SUCESSO: O HyperLogLog atendeu estritamente aos critérios de erro (< 2%) e limite de memória (< 16 KB totais)!")

if __name__ == "__main__":
    test_hyperloglog_memory_and_accuracy()