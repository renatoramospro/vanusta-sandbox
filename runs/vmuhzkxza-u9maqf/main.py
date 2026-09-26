import time
from collections import defaultdict

class Node:
    """Nó da lista duplamente ligada para armazenar chave, valor e frequência."""
    __slots__ = ('key', 'val', 'freq', 'prev', 'next')
    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.freq = 1
        self.prev = None
        self.next = None

class DoublyLinkedList:
    """Lista duplamente ligada para manter nós de mesma frequência em ordem de recência."""
    def __init__(self):
        self.head = Node(None, None)
        self.tail = Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def add_node(self, node):
        nxt = self.head.next
        self.head.next = node
        node.prev = self.head
        node.next = nxt
        nxt.prev = node
        self.size += 1

    def remove_node(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
        self.size -= 1

    def pop_tail(self):
        if self.size == 0:
            return None
        tail_node = self.tail.prev
        self.remove_node(tail_node)
        return tail_node

class LFUCache:
    """
    Implementação de Cache LFU (Least Frequently Used) com complexidade esperada O(1)
    para operações get e put.
    """
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.key_to_node = {}  # Mapeia key -> Node
        self.freq_to_list = defaultdict(DoublyLinkedList)  # Mapeia freq -> DoublyLinkedList

    def _update_freq(self, node: Node) -> None:
        freq = node.freq
        self.freq_to_list[freq].remove_node(node)
        
        if freq == self.min_freq and self.freq_to_list[freq].size == 0:
            self.min_freq += 1
            
        node.freq += 1
        self.freq_to_list[node.freq].add_node(node)

    def get(self, key: int) -> int:
        if key not in self.key_to_node:
            return -1
        node = self.key_to_node[key]
        self._update_freq(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if self.capacity <= 0:
            return

        if key in self.key_to_node:
            node = self.key_to_node[key]
            node.val = value
            self._update_freq(node)
            return

        if len(self.key_to_node) >= self.capacity:
            # Remove o elemento menos frequente (e mais antigo em caso de empate - LRU)
            lru_list = self.freq_to_list[self.min_freq]
            evict_node = lru_list.pop_tail()
            if evict_node:
                del self.key_to_node[evict_node.key]

        # Insere o novo nó com frequência 1
        new_node = Node(key, value)
        self.key_to_node[key] = new_node
        self.freq_to_list[1].add_node(new_node)
        self.min_freq = 1

def run_tests():
    print("Iniciando testes rigorosos do Cache LFU...")

    # 1. Teste de Correção Funcional e Casos de Borda (Empate / min_freq)
    cache = LFUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    assert cache.get(1) == 10, "Erro: get(1) deveria retornar 10"
    
    # Inserção de nova chave deve remover a menos frequente (chave 2, pois chave 1 foi acessada)
    cache.put(3, 30)
    assert cache.get(2) == -1, "Erro: chave 2 deveria ter sido evictada"
    assert cache.get(3) == 30, "Erro: get(3) deveria retornar 30"
    
    # Consulta a chave inexistente não deve corromper o estado
    assert cache.get(999) == -1, "Erro: consulta a chave ausente deve retornar -1"
    print("Teste funcional básico e de borda: APROVADO.")

    # 2. Benchmark de Throughput (10.000+ ops/sec)
    iterations = 50000
    total_operations = iterations * 2  # 1 put e 1 get por iteração
    perf_cache = LFUCache(1000)
    
    start_time = time.time()
    for i in range(iterations):
        perf_cache.put(i % 1500, i)
        perf_cache.get(i % 1200)
    duration = time.time() - start_time

    ops_per_sec = total_operations / duration
    print(f"Executadas {iterations} iterações ({total_operations} operações totais) em {duration:.4f} segundos ({ops_per_sec:.2f} ops/sec).")
    assert ops_per_sec > 10000, f"Desempenho abaixo do esperado: {ops_per_sec} ops/sec"
    print("Teste de throughput (10.000+ ops/sec): APROVADO.")

    # 3. Medição explícita de Hit Rate (> 90%)
    hit_cache = LFUCache(100)
    for i in range(100):
        hit_cache.put(i, i * 10)
    
    hits = 0
    total_lookups = 10000
    # Cenário de acesso repetitivo (80% dos acessos focados em 20% das chaves)
    for i in range(total_lookups):
        key = (i % 20) if (i % 10 < 9) else (i % 100)
        if hit_cache.get(key) != -1:
            hits += 1
            
    hit_rate = (hits / total_lookups) * 100
    print(f"Taxa de acerto (Hit Rate) medida: {hit_rate:.2f}%")
    assert hit_rate > 90.0, f"Hit rate insuficiente: {hit_rate}%"
    print("Teste de Taxa de Acerto (>90%): APROVADO.")

    print("Nota teórica: A complexidade O(1) é esperada/amortizada, dependendo da garantia da tabela hash em Python.")

if __name__ == "__main__":
    run_tests()