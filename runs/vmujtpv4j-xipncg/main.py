import random

class BuddyAllocator:
    def __init__(self, total_size_power=22):  # 2^22 = 4.194.304 bytes (4 MB)
        self.min_order = 4   # Bloco mínimo de 2^4 = 16 bytes
        self.max_order = total_size_power
        self.total_size = 1 << self.max_order
        
        # Simulação da memória física usando um bytearray
        self.memory = bytearray(self.total_size)
        
        # Estrutura para rastrear blocos livres por ordem: sets de offsets iniciais
        self.free_blocks = {i: set() for i in range(self.min_order, self.max_order + 1)}
        self.free_blocks[self.max_order].add(0)
        
        # Mapeamento de blocos alocados: offset -> ordem
        self.allocated_blocks = {}

    def _get_order(self, size):
        # Encontra a menor ordem (potência de 2) que comporta o tamanho solicitado + metadados
        order = self.min_order
        needed = size
        while (1 << order) < needed:
            order += 1
        return max(order, self.min_order)

    def allocate(self, size):
        order = self._get_order(size)
        
        # Procura um bloco livre na ordem necessária ou superior
        current_order = order
        while current_order <= self.max_order and not self.free_blocks[current_order]:
            current_order += 1
            
        if current_order > self.max_order:
            raise MemoryError("Out of Memory: Nenhum bloco disponível.")
            
        # Remove o bloco encontrado da lista de livres
        block = self.free_blocks[current_order].pop()
        
        # Se o bloco for maior que o necessário, fazemos o split recursivo
        while current_order > order:
            current_order -= 1
            buddy = block + (1 << current_order)
            self.free_blocks[current_order].add(buddy)
            
        self.allocated_blocks[block] = order
        return block

    def free(self, block):
        if block not in self.allocated_blocks:
            raise ValueError(f"Ponteiro inválido ou já liberado: {block}")
            
        order = self.allocated_blocks.pop(block)
        
        # Tenta fundir com o buddy recursivamente
        while order < self.max_order:
            buddy = block ^ (1 << order) # XOR calcula o endereço do buddy
            if buddy in self.free_blocks[order]:
                self.free_blocks[order].remove(buddy)
                block = min(block, buddy)
                order += 1
            else:
                break
                
        self.free_blocks[order].add(block)

    def get_external_fragmentation(self):
        total_free = 0
        max_free = 0
        for order, blocks in self.free_blocks.items():
            block_size = 1 << order
            count = len(blocks)
            total_free += count * block_size
            if count > 0 and block_size > max_free:
                max_free = block_size
                
        if total_free == 0:
            return 0.0
        return (total_free - max_free) / total_free

    def verify_no_leak(self):
        # O teste de vazamento exige que exatamente o bloco total esteja livre na ordem máxima
        return len(self.free_blocks[self.max_order]) == 1 and 0 in self.free_blocks[self.max_order] and len(self.allocated_blocks) == 0

# Testes de Execução e Validação
def run_tests():
    print("=== INICIALIZANDO BUDDY SYSTEM ALLOCATOR (4MB) ===")
    allocator = BuddyAllocator(total_size_power=22) # 4 MB
    
    # 1. Cenários Determinísticos (exigidos pelo Arquiteto)
    print("\n[Teste 1] Cenário Determinístico: Alocações de 1 byte repetidas e liberações inversas...")
    allocated_addrs = []
    for _ in range(100):
        addr = allocator.allocate(1)
        allocated_addrs.append(addr)
        
    print(f"Alocados 100 blocos de 1 byte. Fragmentação atual: {allocator.get_external_fragmentation():.4f}")
    
    # Liberação em ordem inversa
    for addr in reversed(allocated_addrs):
        allocator.free(addr)
        
    assert allocator.verify_no_leak(), "Falha: Vazamento de memória detectado após teste determinístico!"
    print("[Sucesso] Teste determinístico concluído sem vazamentos.")

    # 2. Cenário Estocástico: 1000 operações aleatórias
    print("\n[Teste 2] Cenário Estocástico: 1000 operações aleatórias de alocação/liberação...")
    random.seed(42)
    active_allocations = []
    max_frag_observed = 0.0
    
    for i in range(1000):
        # Decidir aleatoriamente entre alocar (70%) ou liberar (30%) se houver alocações ativas
        if active_allocations and random.random() < 0.3:
            addr = active_allocations.pop(random.randrange(len(active_allocations)))
            allocator.free(addr)
        else:
            try:
                # Tamanhos variando entre 16 bytes e 64 KB
                size = random.randint(16, 65536)
                addr = allocator.allocate(size)
                active_allocations.append(addr)
            except MemoryError:
                pass # Ignora OOM se a memória estiver temporariamente saturada
                
        frag = allocator.get_external_fragmentation()
        if frag > max_frag_observed:
            max_frag_observed = frag

    print(f"Operações concluídas. Pico de fragmentação externa observado: {max_frag_observed * 100:.2f}%")
    assert max_frag_observed < 0.15, f"Falha: Fragmentação externa ({max_frag_observed*100:.2f}%) excedeu o limite de 15%!"
    print("[Sucesso] Pico de fragmentação abaixo do limite de 15%.")

    # Limpar todas as alocações restantes para validar o vazamento final
    print("\n[Teste 3] Verificação final de vazamento de memória...")
    while active_allocations:
        addr = active_allocations.pop()
        allocator.free(addr)
        
    assert allocator.verify_no_leak(), "Falha: Vazamento de memória detectado no teste final!"
    print("[Sucesso] Verificação final concluída: 100% da memória foi recuperada e fundida (Sem vazamentos).")
    print("\n=== TODOS OS CRITÉRIOS DE SUCESSO FORAM ATENDIDOS COM ÊXITO ===")

if __name__ == "__main__":
    run_tests()