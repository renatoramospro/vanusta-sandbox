import pytest
from memory_manager import NonContiguousMemoryManager, BadMemoryManager

def test_memory_manager_operations_and_fragmentation():
    # Pool de 1 MiB
    manager = NonContiguousMemoryManager(1024 * 1024)
    allocated_offsets = []

    sizes = [1024, 2048, 4096, 8192, 16384] # Blocos de 1KB a 16KB

    # Executa 100 operações mistas (alocações e desalocações)
    for i in range(100):
        if i % 3 == 0 and allocated_offsets:
            # Desaloca o bloco mais antigo
            offset_to_free = allocated_offsets.pop(0)
            manager.free(offset_to_free)
        else:
            size = sizes[i % len(sizes)]
            offset = manager.allocate(size)
            if offset != -1:
                allocated_offsets.append(offset)

        # Valida que a fragmentação externa não ultrapassa 5% em nenhuma etapa
        frag = manager.get_external_fragmentation()
        assert frag <= 5.0, fiter_msg := f"Falha na iteração {i}: fragmentação externa de {frag:.2f}% excedeu o limite de 5%"

    print(f"Sucesso: 100 operações executadas com fragmentação final de {manager.get_external_fragmentation():.2f}%")

def test_anti_pattern_fragmentation():
    manager = BadMemoryManager(1024 * 1024)
    offsets = []
    for _ in range(15):
        off = manager.allocate(10240)
        if off != -1:
            offsets.append(off)

    # Desaloca blocos alternados para criar fragmentação severa sem coalescência
    for off in offsets[::2]:
        manager.free(off)

    frag = manager.get_external_fragmentation()
    print(f"[Contraexemplo] Fragmentação sem coalescing: {frag:.2f}%")
    
    # O anti-padrão DEVE resultar em fragmentação alta (> 5%)
    assert frag > 5.0, f"O anti-padrão deveria falhar por alta fragmentação, mas obteve {frag:.2f}%"