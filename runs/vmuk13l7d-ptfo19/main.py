path=slab_allocator.py
import time
import random

class Slab:
    def __init__(self, slab_id, object_size, objects_per_slab=16):
        self.slab_id = slab_id
        self.object_size = object_size
        self.objects_per_slab = objects_per_slab
        self.slab_size = object_size * objects_per_slab
        self.memory = bytearray(self.slab_size)
        
        # Freelist embutida baseada em pilha (LIFO) para operações estritamente O(1)
        # Inicialmente todos os slots estão livres, ordenados do último para o primeiro para pop() eficiente.
        self.free_list = list(range(objects_per_slab - 1, -1, -1))
        
        # Bitmap/Set de slots alocados para validação O(1) de ownership e prevenção de double free
        self.allocated_slots = set()
        self.allocated_count = 0

    def is_full(self):
        return len(self.free_list) == 0

    def is_empty(self):
        return self.allocated_count == 0

    def allocate(self):
        if self.is_full():
            return None
        # pop() no final da lista Python é O(1) amortizado
        slot_index = self.free_list.pop()
        self.allocated_slots.add(slot_index)
        self.allocated_count += 1
        return slot_index

    def free(self, slot_index):
        # Validação rigorosa de segurança:
        # 1. Verificar limites físicos do slab
        if not (0 <= slot_index < self.objects_per_slab):
            raise ValueError(f"Erro de Segurança: Índice de slot {slot_index} fora dos limites [0, {self.objects_per_slab-1}].")
        
        # 2. Verificar se o slot realmente está alocado (previne Double Free)
        if slot_index not in self.allocated_slots:
            raise ValueError(f"Erro de Segurança: Double free ou tentativa de liberar slot não alocado ({slot_index}).")
        
        # Remove do set de alocados e retorna para a freelist em O(1)
        self.allocated_slots.remove(slot_index)
        self.free_list.append(slot_index)
        self.allocated_count -= 1
        return True


class KMemCache:
    def __init__(self, name, object_size, objects_per_slab=16):
        self.name = name
        self.object_size = object_size
        self.objects_per_slab = objects_per_slab
        self.slabs = []
        self.next_slab_id = 0

    def _get_or_create_slab(self):
        # Procura por um slab com espaço livre
        for slab in self.slabs:
            if not slab.is_full():
                return slab
        
        # Se nenhum slab tiver espaço, cria um novo (O(1) amortizado)
        new_slab = Slab(self.next_slab_id, self.object_size, self.objects_per_slab)
        self.next_slab_id += 1
        self.slabs.append(new_slab)
        return new_slab

    def allocate(self):
        slab = self._get_or_create_slab()
        slot_index = slab.allocate()
        # Retorna um handle seguro contendo a referência ao slab e ao slot
        return {"slab_id": slab.slab_id, "slab": slab, "slot_index": slot_index}

    def free(self, handle):
        slab = handle["slab"]
        slot_index = handle["slot_index"]
        
        # Validação de ownership: garante que o slab pertence a este cache
        if slab not in self.slabs:
            raise ValueError("Erro de Segurança: Tentativa de liberar objeto em cache incorreto (violação de ownership).")
        
        slab.free(slot_index)
        
        # Mitigação para cargas esparsas: se o slab estiver totalmente vazio e houver mais de um slab,
        # podemos removê-lo para evitar desperdício excessivo de memória (fragmentação interna/externa).
        if slab.is_empty() and len(self.slabs) > 1:
            self.slabs.remove(slab)

    def internal_fragmentation(self):
        total_reserved_bytes = len(self.slabs) * (self.object_size * self.objects_per_slab)
        if total_reserved_bytes == 0:
            return 0.0
        
        total_used_payload = sum(slab.allocated_count * self.object_size for slab in self.slabs)
        wasted_bytes = total_reserved_bytes - total_used_payload
        return wasted_bytes / total_reserved_bytes


def run_tests():
    print("=== Iniciando Testes Corrigidos do Slab Allocator ===")
    
    cache = KMemCache(name="object_cache_64", object_size=64, objects_per_slab=32)
    handles = []

    # Teste de Carga Densa (10.000 alocações)
    start_time = time.perf_counter()
    for _ in range(10000):
        handle = cache.allocate()
        handles.append(handle)
    alloc_time = time.perf_counter() - start_time
    print(f"10.000 alocações realizadas em {alloc_time:.4f} segundos.")

    frag = cache.internal_fragmentation()
    print(f"Fragmentação interna com carga total: {frag * 100:.2f}%")
    assert frag < 0.10, f"Erro: Fragmentação muito alta: {frag*100:.2f}%"

    # Teste de Segurança: Double Free e Índice Inválido
    try:
        cache.free(handles[0]) # Primeira liberação (válida)
        cache.free(handles[0]) # Segunda liberação (deve falhar por double free)
        raise AssertionError("Deveria ter lançado ValueError para double free!")
    except ValueError as e:
        print(f"Segurança validada com sucesso (Double Free bloqueado): {e}")

    try:
        invalid_handle = {"slab_id": handles[1]["slab_id"], "slab": handles[1]["slab"], "slot_index": 9999}
        cache.free(invalid_handle)
        raise AssertionError("Deveria ter lançado ValueError para índice fora dos limites!")
    except ValueError as e:
        print(f"Segurança validada com sucesso (Índice inválido bloqueado): {e}")

    # Liberação normal de 5.000 objetos
    random.shuffle(handles[1:])
    start_time = time.perf_counter()
    for handle in handles[1:5001]:
        cache.free(handle)
    free_time = time.perf_counter() - start_time
    print(f"5.000 liberações realizadas em {free_time:.4f} segundos.")
    print("=== Testes de Correção Concluídos com Sucesso ===")

if __name__ == "__main__":
    run_tests()