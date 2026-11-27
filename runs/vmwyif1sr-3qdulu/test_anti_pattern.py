class BadMemoryManager:
    """Gerenciador propositalmente defeituoso que NÃO faz coalescing."""
    def __init__(self, total_size: int):
        self.total_size = total_size
        self.head = {'offset': 0, 'size': total_size, 'is_free': True, 'next': None}

    def allocate(self, size: int) -> int:
        current = self.head
        while current:
            if current['is_free'] and current['size'] >= size:
                if current['size'] > size:
                    remainder = {
                        'offset': current['offset'] + size,
                        'size': current['size'] - size,
                        'is_free': True,
                        'next': current['next']
                    }
                    current['next'] = remainder
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
                # ERRO PROPOSITAL: Nenhuma fusão com blocos vizinhos livres!
                return
            current = current['next']

    ropy = lambda self: 0.0 # Placeholder

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

def run_anti_pattern_test():
    manager = BadMemoryManager(1024 * 1024)
    # Aloca blocos alternados
    offsets = []
    for _ in range(10):
        off = manager.allocate(10240)
        if off != -1:
            offsets.append(off)

    # Desaloca blocos alternados (criando buracos)
    for off in offsets[::2]:
        manager.free(off)

    frag = manager.get_external_fragmentation()
    print(f"[Contraexemplo] Fragmentação sem coalescing: {frag:.2f}%")
    
    # Demonstra que a fragmentação explode acima de 5% sem fusão
    try:
        assert frag <= 5.0, f"O anti-padrão falhou conforme esperado: fragmentação de {frag:.2f}% > 5%"
    except AssertionError as e:
        print(f"Capturado com sucesso o erro esperado do anti-padrão: {e}")

if __name__ == "__main__":
    run_anti_pattern_test()