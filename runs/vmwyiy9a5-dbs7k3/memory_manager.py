class MemoryBlock:
    def __init__(self, offset: int, size: int, is_free: bool = True):
        self.offset = offset
        self.size = size
        self.is_free = is_free
        self.prev = None
        self.next = None

class NonContiguousMemoryManager:
    def __init__(self, total_size: int):
        self.total_size = total_size
        self.head = MemoryBlock(0, total_size, is_free=True)

    def allocate(self, size: int) -> int:
        best_block = None
        current = self.head
        
        # Estratégia Best-Fit: busca o menor bloco livre que atende ao tamanho requisitado
        while current:
            if current.is_free and current.size >= size:
                if best_block is None or current.size < best_block.size:
                    best_block = current
            current = current.next

        if best_block is None:
            return -1  # Sem memória suficiente

        # Realiza o split do bloco se ele for maior que o necessário
        if best_block.size > size:
            remaining_size = best_block.size - size
            new_block = MemoryBlock(best_block.offset + size, remaining_size, is_free=True)
            
            new_block.next = best_block.next
            new_block.prev = best_block
            if best_block.next:
                best_block.next.prev = new_block
            best_block.next = new_block
            
            best_block.size = size

        best_block.is_free = False
        return best_block.offset

    def free(self, offset: int):
        current = self.head
        while current:
            if current.offset == offset and not current.is_free:
                current.is_free = True
                self._coalesce(current)
                return
            current = current.next
        raise ValueError(f"Bloco com offset {offset} não encontrado ou já está livre.")

    def _coalesce(self, block: MemoryBlock):
        # Fusão com o bloco sucessor (next) se livre
        if block.next and block.next.is_free:
            block.size += block.next.size
            block.next = block.next.next
            if block.next:
                block.next.prev = block

        # Fusão com o bloco antecessor (prev) se livre
        if block.prev and block.prev.is_free:
            block.prev.size += block.size
            block.prev.next = block.next
            if block.next:
                block.next.prev = block.prev
            block = block.prev

    def get_external_fragmentation(self) -> float:
        total_free = 0
        max_free_block = 0
        current = self.head
        
        while current:
            if current.is_free:
                total_free += current.size
                if current.size > max_free_block:
                    max_free_block = current.size
            current = current.next

        if total_free == 0:
            return 0.0

        # Métrica clássica: (1 - (tamanho do maior bloco livre / soma de todos os blocos livres)) * 100
        fragmentation = (1.0 - (max_free_block / total_free)) * 100.0
        return fragmentation


class BadMemoryManager(NonContiguousMemoryManager):
    """Contraexemplo: Gerenciador que NÃO realiza coalescência (coalescing) de blocos livres."""
    def _coalesce(self, block: MemoryBlock):
        # Intencionalmente vazio para demonstrar fragmentação externa severa
        pass