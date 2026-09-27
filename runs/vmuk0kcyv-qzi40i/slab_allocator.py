import time
import random

class Slab:
    def __init__(self, object_size, objects_per_slab=16):
        self.object_size = object_size
        self.objects_per_slab = objects_per_slab
        self.slab_size = object_size * objects_per_slab
        # Memória simulada como um bytearray contínuo
        self.memory = bytearray(self.slab_size)
        
        # Lista encadeada livre embutida (armazena os índices dos slots livres)
        self.free_list = list(range(objects_per_slab))
        self.allocated_count = 0

    def is_full(self):
        return len(self.free_list) == 0

    def is_empty(self):
        return self.allocated_count == 0

    def allocate(self):
        if self.is_full():
            return None
        slot_index = self.free_list.pop(0)
        self.allocated_count += 1
        return slot_index

    def free(self, slot_index):
        # Validação simples para evitar double free
        if slot_index not in self.free_list:
            self.free_list.append(slot_index)
            self.allocated_count -= 1
            return True
        return False


class KMemCache:
    def __init__(self, name, object_size, objects_per_slab=32):
        self.name = name
        self.object_size = object_size
        self.objects_per_slab = objects_per_slab
        self.slabs = []
        # Mantém referência rápida a um slab com espaço livre O(1)
        self.active_slab_index = 0

    def _find_free_slab(self):
        for i, slab in enumerate(self.slabs):
            if not slab.is_full():
                return i
        return -1

    def alloc(self):
        # Procura slab com espaço livre
        if not self.slabs or self.slabs[self.active_slab_index].is_full():
            idx = self._find_free_slab()
            if idx == -1:
                # Cria novo slab
                new_slab = Slab(self.object_size, self.objects_per_slab)
                self.slabs.append(new_slab)
                self.active_slab_index = len(self.slabs) - 1
            else:
                self.active_slab_index = idx

        slab = self.slabs[self.active_slab_index]
        slot_index = slab.allocate()
        return (self.active_slab_index, slot_index)

    def free(self, address_tuple):
        slab_idx, slot_idx = address_tuple
        if slab_idx < len(self.slabs):
            slab = self.slabs[slab_idx]
            slab.free(slot_idx)
            # Se o slab ficar totalmente vazio e houver mais de um slab, podemos liberá-lo (opcional, aqui mantemos)
            self.active_slab_index = slab_idx

    def internal_fragmentation(self):
        """
        Calcula a fragmentação interna:
        Espaço desperdiçado dentro dos slabs alocados devido ao alinhamento/tamanho fixo
         versus o espaço efetivamente utilizado pelos objetos ativos.
        """
        total_bytes_reserved = len(self.slabs) * self.object_size * self.objects_per_slab
        if total_bytes_reserved == 0:
            return 0.0
        
        total_bytes_used = sum(slab.allocated_count * self.object_size for slab in self.slabs)
        
        # Fragmentação = (Espaço Reservado - Espaço Útil) / Espaço Reservado
        frag = (total_bytes_reserved - total_bytes_used) / total_bytes_reserved
        return frag


def run_tests():
    print("=== Iniciando Testes do Slab Allocator ===")
    
    # Criando cache para objetos de 64 bytes
    cache = KMemCache(name="cache_64b", object_size=64, objects_per_slab=64)
    
    handles = []
    start_time = time.perf_counter()
    
    # 10.000 alocações
    for _ in range(10000):
        handle = cache.alloc()
        handles.append(handle)
        
    alloc_time = time.perf_counter() - start_time
    print(horas := f"10.000 alocações realizadas em {alloc_time:.4f} segundos.")
    
    frag = cache.internal_fragmentation()
    print(f"Fragmentação interna com carga total: {frag * 100:.2f}%")
    
    # Validação de sucesso de fragmentação (< 10% quando saturado)
    assert frag < 0.10, f"Erro: Fragmentação muito alta: {frag*100:.2f}%"

    # Liberação aleatória simulando comportamento real (Amortizado O(1))
    random.shuffle(handles)
    start_time = time.perf_counter()
    
    for handle in handles[:5000]:
        cache.free(handle)
        
    free_time = time.perf_counter() - start_time
    print(f"5.000 liberações realizadas em {free_time:.4f} segundos.")
    
    print("=== Testes concluídos com sucesso ===")

if __name__ == "__main__":
    run_tests()