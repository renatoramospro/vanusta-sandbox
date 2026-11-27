import math
import random

class L1CacheSimulator:
    def __init__(self, capacity_bytes=32768, block_size=64, associativity=4, hit_time=1, miss_penalty=100, policy="LRU"):
        self.capacity = capacity_bytes
        self.block_size = block_size
        self.assoc = associativity
        self.hit_time = hit_time
        self.miss_penalty = miss_penalty
        self.policy = policy.upper()

        # Derivações estruturais
        self.num_blocks = self.capacity // self.block_size
        self.num_sets = self.num_blocks // self.assoc

        # Validação de parâmetros físicos
        if (self.capacity % self.block_size != 0) or (self.num_blocks % self.assoc != 0):
            raise ValueError("Configuração inválida: Capacidade, tamanho de bloco e associatividade incompatíveis.")

        # Cálculo de bits de endereço
        self.offset_bits = int(math.log2(self.block_size))
        self.index_bits = int(math.log2(self.num_sets))
        # Assumindo endereços de 32 bits
        self.tag_bits = 32 - (self.index_bits + self.offset_bits)

        # Estrutura do Cache: { set_index: [ [tag, data, lru_counter/fifo_order], ... até assoc ] }
        self.cache = {i: [] for i in range(self.num_sets)}
        
        # Contadores de desempenho
        self.hits = 0
        self.misses = 0
        self.access_counter = 0

    def _decode_address(self, address):
        """Decodifica o endereço físico em Offset, Index e Tag."""
        offset = address & ((1 << self.offset_bits) - 1)
        index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1)
        tag = address >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    def access(self, address):
        """Simula um acesso à memória (leitura/escrita) no cache L1."""
        self.access_counter += 1
        tag, index, _ = self._decode_address(address)
        set_lines = self.cache[index]

        # Verifica se a tag já está presente no conjunto (Hit)
        for i, line in enumerate(set_lines):
            if line[0] == tag:
                self.hits += 1
                # Atualiza política de substituição
                if self.policy == "LRU":
                    # Move para o final (mais recentemente usado)
                    item = set_lines.pop(i)
                    item[2] = self.access_counter
                    set_lines.append(item)
                return True # Hit

        # Se chegou aqui, é Miss
        self.misses += 1
        new_line = [tag, f"data_block_{address}", self.access_counter]

        if len(set_lines) < self.assoc:
            # Conjunto não está cheio, insere diretamente
            set_lines.append(new_line)
        else:
            # Conjunto cheio, aplica política de substituição
            if self.policy == "LRU":
                # Remove o elemento com menor contador (menos recentemente usado)
                lru_idx = min(range(len(set_lines)), key=lambda idx: set_lines[idx][2])
                set_lines.pop(lru_idx)
            elif self.policy == "FIFO":
                # Remove o elemento mais antigo (menor timestamp de inserção)
                fifo_idx = min(range(len(set_lines)), key=lambda idx: set_lines[idx][2])
                set_lines.pop(fifo_idx)
            set_lines.append(new_line)
        
        return False # Miss

    def get_hit_rate(self):
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def get_amat(self):
        total = self.hits + self.misses
        if total == 0:
            return float(self.hit_time)
        miss_rate = self.misses / total
        return self.hit_time + (miss_rate * self.miss_penalty)

    def reset_stats(self):
        self.hits = 0
        self.misses = 0
        self.access_counter = 0


def generate_scenarios():
    """Gera 10 cenários de acesso distintos, categorizados em Típicos e Adversariais."""
    scenarios = []
    
    # --- Cenários Típicos (Alta Localidade / Esperado >90% Hit Rate) ---
    # 1. Acesso sequencial pequeno (dentro do cache)
    scenarios.append(("Sequential_Small", [i * 64 for i in range(100)]))
    
    # 2. Loop apertado (reuso temporal intenso)
    loop_addrs = [i * 64 for i in range(16)]
    scenarios.append(("Tight_Loop", loop_addrs * 50))
    
    # 3. Mix de loops com sobreposição
    scenarios.append(("Loop_Mix", [i * 64 for i in range(32)] * 10))
    
    # 4. Alta localidade temporal (foco em poucos blocos)
    scenarios.append(("High_Temporal", [random.choice([0, 64, 128, 192]) for _ in range(500)]))
    
    # 5. Blocos pequenos repetidos
    scenarios.append(("Small_Block_Repeated", [64 * (i % 8) for i in range(400)]))
    
    # 6. Ping-pong entre dois working sets complementares
    ping_pong = ([0, 64, 128] * 20) + ([1024, 1088, 1152] * 20)
    scenarios.append(("Ping_Pong", ping_pong))
    
    # 7. Otimized Locality (matriz sequencial com stride de linha única)
    scenarios.append(("Optimized_Locality", [i * 64 for i in range(256)]))

    # --- Cenários Adversariais (Estresse / Cache Thrashing por Set Aliasing) ---
    # 8. Strided Access estruturado em múltiplos exatos de set aliasing
    # Com 32KB, 64B/bloco, 4-way -> 128 sets. Stride de 128 * 64 = 8192 mapeia no mesmo set.
    scenarios.append(("Strided_Access", [i * 8192 for i in range(100)]))
    
    # 9. Large Linear Scan (excede capacidade do cache L1 de 32KB)
    scenarios.append(("Large_Linear_Scan", [i * 64 for i in range(2000)]))
    
    # 10. Prime Stride (conflito severo de ways)
    scenarios.append(("Prime_Stride", [i * 16384 for i in range(100)]))

    return scenarios


if __name__ == "__main__":
    print("=== Simulador de Cache L1: Validação com Critério Refinado ===")
    cache = L1CacheSimulator(capacity_bytes=32768, block_size=64, associativity=4, hit_time=1, miss_penalty=100, policy="LRU")
    
    scenarios = generate_scenarios()
    
    print(f"\nParâmetros do Cache:")
    print(f"- Capacidade: {cache.capacity} bytes")
    print(f"- Tamanho do Bloco: {cache.block_size} bytes")
    print(f"- Associatividade: {cache.assoc}-way")
    print(f"- Número de Sets: {cache.num_sets}")
    print(f"- Bits de Tag / Index / Offset: {cache.tag_bits} / {cache.index_bits} / {cache.offset_bits}\n")

    print(f"{'Cenário':<25} | {'Tipo':<12} | {'Taxa de Acerto (%)':<18} | {'AMAT (ciclos)':<15}")
    print("-" * 78)

    typical_hits_ok = 0
    typical_count = 0
    adversarial_count = 0
    adversarial_handled = 0

    for name, addresses in scenarios:
        cache.reset_stats()
        for addr in addresses:
            cache.access(addr)
        
        hit_rate = cache.get_hit_rate()
        amat = cache.get_amat()
        
        is_adversarial = name in ["Strided_Access", "Large_Linear_Scan", "Prime_Stride"]
        tipo = "Adversarial" if is_adversarial else "Típico"
        
        if is_adversarial:
            adversarial_count += 1
            # Para cenários adversariais, o comportamento esperado de thrashing é detectado (hit rate baixo/zero)
            if hit_rate < 10.0:
                adversarial_handled += 1
        else:
            typical_count += 1
            if hit_rate >= 90.0:
                typical_hits_ok += 1

        print(f"{name:<25} | {tipo:<12} | {hit_rate:>18.2f} | {amat:>15.2f}")

    print("-" * 78)
    print(f"Cenários Típicos com >90% de Hit Rate: {typical_hits_ok}/{typical_count}")
    print(f"Cenários Adversariais isolados com Thrashing esperado (<10%): {adversarial_handled}/{adversarial_count}")

    # Critério de sucesso refinado:
    # 1. 100% dos cenários típicos atingem >90% de hit rate.
    # 2. 100% dos cenários adversariais demonstram o comportamento de conflito esperado (thrashing).
    assert typical_hits_ok == typical_count, "Falha: Cenários típicos não atingiram a meta de >90% de hit rate."
    assert adversarial_handled == adversarial_count, "Falha: Cenários adversariais não se comportaram como esperado."
    
    print("\n[SUCESSO] Validação concluída. O critério refinado foi atendido integralmente.")