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
        # Fusão com o bloco seguinte (direito) se estiver livre
        if block.next and block.next.is_free:
            block.size += block.next.size
            block.next = block.next.next
            if block.next:
                block.next.prev = block

        # Fusão com o bloco anterior (esquerdo) se estiver livre
        if block.prev and block.prev.is_free:
            block.prev.size += block.size
            block.prev.next = block.next
            if block.next:
                block.next.prev = block.prev

    def get_external_fragmentation(self) -> float:
        free_blocks = []
        current = self.head
        while current:
            if current.is_free:
                free_blocks.append(current.size)
            current = current.next

        if not free_blocks or len(free_blocks) == 1:
            return 0.0

        total_free = sum(free_blocks)
        max_free = max(free_blocks)
        
        # Métrica clássica: 100% - (maior bloco livre / soma de todos os blocos livres * 100)
        return 100.0 * (1.0 - (max_free / total_free)) if total_free > 0 else 0.0


class BadMemoryManager:
    """Implementação intencionalmente sem coalescência para demonstrar o anti-padrão."""
    def __init__(self, total_size: int):
        self.total_size = total_size
        self.head = {'offset': 0, 'size': total_size, 'is_free': True, 'next': None, 'prev': None}

    def allocate(self, size: int) -> int:
        current = self.head
        while current:
            if current['is_free'] and current['size'] >= size:
                if current['size'] > size:
                    new_block = {
                        'offset': current['offset'] + size,
                        'size': current['size'] - size,
                        'is_free': True,
                        'next': current['next'],
                        'prev': current
                    }
                    if current['next']:
                        current['next']['prev'] = new_block
                    current['next'] = new_block
                    current['size'] = size
                current['is_free'] = False
                return current['offset']
            current = current['next']
        return -1

    def free(self, offset: int):
        current = self.head
        while current:
            if current['offset'] == offset:
                current['is_free'] = True
                # PROPÓSITO: Omitida a fusão (coalescing) de propósito!
                return
            current = current['next']

    def get_external_fragmentation(self) -> float:
        free_blocks = []
        current = self.head
        while current:
            if current['is_free']:
                free_blocks.append(current['size'])
            current = current['next']
        if not free_blocks or len(free_blocks) == 1:
            return 0.0
        total_free = sum(free_blocks)
        max_free = max(free_blocks)
        return 100.0 * (1.0 - (max_free / total_free)) if total_free > 0 else 0.0