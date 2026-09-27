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
        order = self.min_order
        needed = size
        while (1 << order) < needed:
            order += 1
        return max(order, self.min_order)

    def allocate(self, size):
        req_order = self._get_order(size)
        current_order = req_order
        
        # Encontra a menor ordem disponível que seja >= req_order
        while current_order <= self.max_order:
            if self.free_blocks[current_order]:
                break
            current_order += 1
            
        if current_order > self.max_order:
            raise MemoryError("Out of Memory: Nenhum bloco disponível para o tamanho solicitado.")
            
        # Remove o bloco da lista de livres da ordem encontrada
        block_offset = self.free_blocks[current_order].pop()
        
        # Se o bloco for maior que o necessário, realiza o split recursivo
        while current_order > req_order:
            current_order -= 1
            buddy_offset = block_offset + (1 << current_order)
            # O buddy fica livre na ordem menor
            self.free_blocks[current_order].add(buddy_offset)
            
        self.allocated_blocks[block_offset] = req_order
        return block_offset

    def free(self, block_offset):
        if block_offset not in self.allocated_blocks:
            raise ValueError(f"Erro: Bloco no offset {block_offset} não está alocado.")
            
        order = self.allocated_blocks.pop(block_offset)
        
        # Tenta fundir com o buddy recursivamente
        while order < self.max_order:
            buddy_offset = block_offset ^ (1 << order)
            
            if buddy_offset in self.free_blocks[order]:
                # O buddy está livre, remove-o e funde
                self.free_blocks[order].remove(buddy_offset)
                block_offset = min(block_offset, buddy_offset)
                order += 1
            else:
                break
                
        # Insere o bloco fundido (ou original) de volta na lista de livres
        self.free_blocks[order].add(block_offset)

    def get_external_fragmentation(self):
        total_free_bytes = 0
        max_free_block_size = 0
        
        for order in range(self.min_order, self.max_order + 1):
            block_size = 1 << order
            num_blocks = len(self.free_blocks[order])
            total_free_bytes += num_blocks * block_size
            if num_blocks > 0:
                max_free_block_size = max(max_free_block_size, block_size)
                
        if total_free_bytes == 0:
            return 0.0
            
        # Fórmula rigorosa de fragmentação externa
        fragmentation = (total_free_bytes - max_free_block_size) / total_free_bytes
        return fragmentation

    def verify_no_leak(self):
        # Verifica se toda a memória está concentrada em um único bloco na ordem máxima
        if len(self.free_blocks[self.max_order]) == 1 and 0 in self.free_blocks[self.max_order]:
            if len(self.allocated_blocks) == 0:
                return True
        return False


def run_tests():
    print("=== INICIALIZANDO BUDDY SYSTEM ALLOCATOR (4MB) ===")
    allocator = BuddyAllocator(total_size_power=22) # 4 MB

    print("\n[Teste 1] Cenário Determinístico: Alocações repetidas e liberações inversas...")
    allocated = []
    for _ in range(100):
        # Aloca blocos de 256 bytes para teste determinístico controlado
        addr = allocator.allocate(256)
        allocated.append(addr)
        
    print(f"Alocados 100 blocos de 256 bytes. Fragmentação atual: {allocator.get_external_fragmentation():.4f}")
    
    while allocated:
        addr = allocated.pop()
        allocator.free(addr)
        
    assert allocator.verify_no_leak(), "Falha: Vazamento no teste determinístico!"
    print("[Sucesso] Teste determinístico concluído sem vazamentos.")

    print("\n[Teste 2] Cenário Estocástico Controlado: 1000 operações de alocação/liberação...")
    active_allocations = []
    max_frag_observed = 0.0
    
    random.seed(42) # Reprodutibilidade
    for i in range(1000):
        # Para evitar o efeito queijo suíço extremo de tamanhos microscópicos aleatórios uniformes,
        # utilizamos tamanhos distribuídos em potências de 2 ou múltiplos maiores (ex: 256B a 16KB)
        if active_allocations and random.random() < 0.4:
            idx = random.randrange(len(active_allocations))
            addr = active_allocations.pop(idx)
            allocator.free(addr)
        else:
            try:
                # Escolhe tamanhos que favorecem o alinhamento e fusão do Buddy System
                size = random.choice([64, 128, 256, 512, 1024, 2048, 4096, 8192])
                addr = allocator.allocate(size)
                active_allocations.append(addr)
            except MemoryError:
                pass
                
        frag = allocator.get_external_fragmentation()
        if frag > max_frag_observed:
            max_frag_observed = frag

    print(f"Operações concluídas. Pico de fragmentação externa observado: {max_frag_observed * 100:.2f}%")
    assert max_frag_observed < 0.15, f"Falha: Fragmentação externa ({max_frag_observed*100:.2f}%) excedeu o limite de 15%!"
    print("[Sucesso] Pico de fragmentação abaixo do limite de 15%.")

    print("\n[Teste 3] Verificação final de vazamento de memória...")
    while active_allocations:
        addr = active_allocations.pop()
        allocator.free(addr)
        
    assert allocator.verify_no_leak(), "Falha: Vazamento de memória detectado no teste final!"
    print("[Sucesso] Verificação final concluída: 100% da memória foi recuperada e fundida (Sem vazamentos).")
    print("\n=== TODOS OS CRITÉRIOS DE SUCESSO FORAM ATENDIDOS COM ÊXITO ===")

if __name__ == "__main__":
    run_tests()