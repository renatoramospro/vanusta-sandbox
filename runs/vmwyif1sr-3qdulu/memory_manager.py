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
        # Bloco inicial único cobrindo toda a memória
        self.head = MemoryBlock(offset=0, size=total_size, is_free=True)

    def allocate(self, size: int) -> int:
        """Aloca memória usando Best-Fit. Retorna o offset ou -1 se falhar."""
        current = self.head
        best_block = None

        # Best-Fit: encontrar o menor bloco livre que caiba o tamanho requisitado
        while current is not None:
            if current.is_free and current.size >= size:
                if best_block is None or current.size < best_block.size:
                    best_block = current
            current = current.next

        if best_block is None:
            return -1  # Out of memory

        # Split do bloco se sobrarem bytes suficientes
        if best_block.size > size:
            remainder_size = best_block.size - size
            remainder_block = MemoryBlock(
                offset=best_block.offset + size,
                size=remainder_size,
                is_free=True
            )
            remainder_block.next = best_block.next
            remainder_block.prev = best_block
            if best_block.next:
                best_block.next.prev = remainder_block
            best_block.next = remainder_block
            best_block.size = size

        best_block.is_free = False
        return best_block.offset

    def free(self, offset: int):
        """Desaloca o bloco no offset especificado e executa coalescing."""
        current = self.head
        while current is not None:
            if current.offset == offset and not current.is_free:
                break
            current = current.next

        if current is None:
            raise ValueError(f"Bloco inválido ou já liberado no offset {offset}")

        current.is_free = True

        # Coalescing com o sucessor (next)
        if current.next and current.next.is_free:
            next_block = current.next
            current.size += next_block.size
            current.next = next_block.next
            if next_block.next:
                next_block.next.prev = current

        # Coalescing com o predecessor (prev)
        if current.prev and current.prev.is_free:
            prev_block = current.prev
            prev_block.size += current.size
            prev_block.next = current.next
            if current.next:
                current.next.prev = prev_block

    def get_external_fragmentation(self) -> float:
        """
        Calcula a fragmentação externa:
        Frag = 100 - (Tamanho do Maior Bloco Livre / Soma de Todos os Blocos Livres) * 100
        Se não houver blocos livres ou apenas um, a fragmentação é 0%.
        """
        free_blocks = []
        current = self.head
        while current is not None:
            if current.is_free:
                free_blocks.append(current.size)
            current = current.next

        if not free_blocks or len(free_blocks) == 1:
            return 0.0

        total_free = sum(free_blocks)
        max_free = max(free_blocks)

        if total_free == 0:
            return 0.0

        fragmentation = 100.0 * (1.0 - (max_free / total_free))
        return fragmentation


def run_simulation():
    # Pool de 1 MiB
    pool_size = 1024 * 1024
    manager = NonContiguousMemoryManager(pool_size)

    # Conjunto de tamanhos variados (potências de 2 de 1 KiB a 64 KiB)
    sizes = [1024, 2048, 4096, 8192, 16384, 32768, 65536]
    allocated_blocks = []

    max_frag_observed = 0.0

    print("Iniciando simulação de 100 operações de alocação/desalocação...")

    # Executar 100 operações determinísticas mistas
    for i in range(100):
        # Determinístico baseado no índice para reprodutibilidade
        op_type = (i % 3 != 0)  # ~66% alocações, 33% desalocações

        if op_type or not allocated_blocks:
            # Escolher tamanho baseado no índice
            size = sizes[i % len(sizes)]
            offset = manager.allocate(size)
            if offset != -1:
                allocated_blocks.append((offset, size))
        else:
            # Desalocar o bloco mais antigo na lista
            offset, size = allocated_blocks.pop(0)
            manager.free(offset)

        frag = manager.get_external_fragmentation()
        if frag > max_frag_observed:
            max_frag_observed = frag

    print(f"Simulação concluída.")
    print(f"Pico máximo de fragmentação externa observado: {max_frag_observed:.2f}%")

    # Validação do critério de sucesso (< 5%)
    assert max_frag_observed <= 5.0, f"Falha: Fragmentação máxima de {max_frag_observed:.2f}% excedeu o limite de 5%!"
    print("Sucesso: A fragmentação externa manteve-se rigorosamente abaixo de 5% durante toda a simulação.")

if __name__ == "__main__":
    run_simulation()